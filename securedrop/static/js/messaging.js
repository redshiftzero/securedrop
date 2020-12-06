function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Temp: Investigate best way to sanitize plaintext messages prior to display
function sanitizeString(str) {
    str = str.replace(/[^a-z0-9áéíóúñü \.,_-]/gim,"");
    return str.trim();
}

function removeSendMsg() {
    document.getElementById("success-message").remove();
}

function apiSend( method, url, token, req_body, fn_success_callback, get_response_body = false ) {
    var request = new XMLHttpRequest();
    request.open(method, url, true);
    request.setRequestHeader("Content-Type", "application/json");
    request.setRequestHeader("Authorization", `Token ${token}`);

    request.onreadystatechange = function () {
      if (request.readyState === 4 && request.status === 200) {
        if (get_response_body == true) {
            resp = JSON.parse(this.response)
        }
        fn_success_callback();
      } else {
        // TODO: If error occurs, then we'd need to show some sort of error to the user.
        console.error("err occurred hitting securedrop API")
      }
    };

    if (req_body != null) {
        request.send(JSON.stringify(req_body));
    } else {
        request.send();
    }
}

function onRegistrationSuccess() {
    console.log("registered successfully!")
}

function onPrekeySucccess(session, prekey_data) {
    console.log(`got some ${prekey_data}`)

    // TODO: show error to user if the below call to wasm fails
    session.process_prekey_bundle(
      prekey_data["registration_id"],
      prekey_data["identity_key"],
      prekey_data["journalist_uuid"],
      prekey_data["signed_prekey_id"],
      prekey_data["signed_prekey"],
      prekey_data["prekey_signature"]
      );
    console.log("processed prekey bundle successfully");

    document.getElementById("submit-doc-button").disabled = false;
}


function onReplySucccess(session, reply_data, token) {
    if (reply_data["resp"] == 'NEW_MSG') {
        console.log("got new reply");
        var plaintext = session.decrypt(
            reply_data["journalist_uuid"],
            reply_data["message"],
        );
        console.log(`decrypted new message!: ${plaintext}`);
        // At this point, we might want to store messages somewhere more persistent
        // (e.g. some local browser storage that works while in Private Browsing Mode).
        // Otherwise, when a user refreshes, their messages will be gone.
        // However, we do want this not to persist (should be the case in PBM) such
        // that on subsequent logins, the messages are also gone.

        // Security note: at this point we need to sanitize the plaintext prior to
        // displaying in the browser. For now we use sanitizeString, but we may
        // want to bring in another dependency for this.
        const reply_div = document.createElement("div");
        reply_div.className = "reply";
        const success_blquote = document.createElement("blockquote");
        success_blquote.textContent = sanitizeString(plaintext);
        reply_div.appendChild(success_blquote);
        document.getElementById("replies").appendChild(reply_div);

        // Now send confirmation.
        var message_uuid = reply_data["message_uuid"];
        apiSend( "POST", `http://127.0.0.1:8080/api/v2/messages/confirmation/${message_uuid}`, token, null, onConfirmationSuccess );
    }
}

function onMessageSendSuccess() {
    const success_div = document.createElement("div");
    success_div.id = "success-message"
    const success_emoji = document.createTextNode("sent! ✅");
    success_div.appendChild(success_emoji);
    document.getElementById("below-the-submit").prepend(success_div);
    setTimeout(removeSendMsg, 3000); // Remove this message in 3 seconds
    console.log("sent successfully!")
}

function onConfirmationSuccess() {
    console.log(`sent confirmation of message on server`);
}

function prepareSession( session, needs_registration, securedrop_group, token ) {
    console.log(`we need to register: ${needs_registration}`);

    if (needs_registration == true) {
        var keygen_data = session.generate();  // keygen_data just contains the public parts
        console.log(`signal key generation succeeded: ${keygen_data}`);
        apiSend( "POST", "http://127.0.0.1:8080/api/v2/register", token, keygen_data, onRegistrationSuccess );

        // Todo (when we have multiple journalists): form a group
        // i.e. we'd need to: For each journalist for which we do not have prekeys do the below logic
        // But for now the group is a single journalist.
        var journalist_uuid = securedrop_group;

        var prekey_request = new XMLHttpRequest();
        prekey_request.open("GET", `http://127.0.0.1:8080/api/v2/journalists/${journalist_uuid}/prekey_bundle`, true);
        prekey_request.setRequestHeader("Content-Type", "application/json");
        prekey_request.setRequestHeader("Authorization", `Token ${token}`);

        prekey_request.onreadystatechange = function () {
          if (prekey_request.readyState === 4 && prekey_request.status === 200) {
            var prekey_data = JSON.parse(this.response)
            onPrekeySucccess(session, prekey_data);
          }
        };
        prekey_request.send();
      } else {
        document.getElementById("submit-doc-button").disabled = false;
      }

      console.log(`user is registered, waiting for message send`);
}

function messageEncryptAndSend( session, journalist_uuid, token ) {
    var message_text = document.getElementById("message-input").value;
    // TODO: Don't do anything if message empty
    var ciphertext = session.encrypt(journalist_uuid, message_text);
    console.log(`message text: ${message_text}`);
    console.log(`ciphertext: ${ciphertext}`);

    var payload = {"message": ciphertext,};
    apiSend( "POST", `http://127.0.0.1:8080/api/v2/journalists/${journalist_uuid}/messages`, token, payload, onMessageSendSuccess );

    // Now reset UI for next message
    document.getElementById("message-input").value = "";
}

function messageDecryptAndSend( session, token ) {
    // Download
    var request = new XMLHttpRequest();
    request.open("GET", "http://127.0.0.1:8080/api/v2/messages", true);
    request.setRequestHeader("Content-Type", "application/json");
    request.setRequestHeader("Authorization", `Token ${token}`);

    request.onreadystatechange = function () {
    if (request.readyState === 4 && request.status === 200) {
        var reply_data = JSON.parse(this.response);
        onReplySucccess(session, reply_data, token);
        };
    request.send();
    }
}
