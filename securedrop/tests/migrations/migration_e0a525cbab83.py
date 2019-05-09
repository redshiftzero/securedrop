# -*- coding: utf-8 -*-

import random
import string
import uuid

from sqlalchemy import text
from sqlalchemy.exc import NoSuchColumnError

from db import db
from journalist_app import create_app
from .helpers import (random_bool, random_bytes, random_chars, random_datetime, random_name,
                      random_username, bool_or_none)


random.seed('⎦˚◡˚⎣')


def add_source():
    filesystem_id = random_chars(96) if random_bool() else None
    params = {
        'uuid': str(uuid.uuid4()),
        'filesystem_id': filesystem_id,
        'journalist_designation': random_chars(50),
        'flagged': bool_or_none(),
        'last_updated': random_datetime(nullable=True),
        'pending': bool_or_none(),
        'interaction_count': random.randint(0, 1000),
    }
    sql = '''
    INSERT INTO sources (uuid, filesystem_id, journalist_designation, flagged, last_updated,
        pending, interaction_count)
    VALUES (:uuid, :filesystem_id, :journalist_designation, :flagged, :last_updated, :pending,
        :interaction_count)
    '''
    db.engine.execute(text(sql), **params)


def add_journalist():
    if random_bool():
        otp_secret = random_chars(16, string.ascii_uppercase + '234567')
    else:
        otp_secret = None

    is_totp = random_bool()
    if is_totp:
        hotp_counter = 0 if random_bool() else None
    else:
        hotp_counter = random.randint(0, 10000) if random_bool() else None

    last_token = random_chars(6, string.digits) if random_bool() else None

    params = {
        'username': random_username(),
        'pw_salt': random_bytes(1, 64, nullable=True),
        'pw_hash': random_bytes(32, 64, nullable=True),
        'is_admin': bool_or_none(),
        'otp_secret': otp_secret,
        'is_totp': is_totp,
        'hotp_counter': hotp_counter,
        'last_token': last_token,
        'created_on': random_datetime(nullable=True),
        'last_access': random_datetime(nullable=True),
        'passphrase_hash': random_bytes(32, 64, nullable=True)
    }
    sql = '''
    INSERT INTO journalists (username, pw_salt, pw_hash, is_admin, otp_secret, is_totp,
        hotp_counter, last_token, created_on, last_access, passphrase_hash)
    VALUES (:username, :pw_salt, :pw_hash, :is_admin, :otp_secret, :is_totp, :hotp_counter,
        :last_token, :created_on, :last_access, :passphrase_hash);
    '''
    db.engine.execute(text(sql), **params)


def add_journalist_after_migration(set_first_name=True, set_last_name=True):
    if random_bool():
        otp_secret = random_chars(16, string.ascii_uppercase + '234567')
    else:
        otp_secret = None

    is_totp = random_bool()
    if is_totp:
        hotp_counter = 0 if random_bool() else None
    else:
        hotp_counter = random.randint(0, 10000) if random_bool() else None

    last_token = random_chars(6, string.digits) if random_bool() else None

    first_name = random_name() if set_first_name else None
    last_name = random_name() if set_last_name else None

    params = {
        'username': random_username(),
        'first_name': first_name,
        'last_name': last_name,
        'pw_salt': random_bytes(1, 64, nullable=True),
        'pw_hash': random_bytes(32, 64, nullable=True),
        'is_admin': bool_or_none(),
        'otp_secret': otp_secret,
        'is_totp': is_totp,
        'hotp_counter': hotp_counter,
        'last_token': last_token,
        'created_on': random_datetime(nullable=True),
        'last_access': random_datetime(nullable=True),
        'passphrase_hash': random_bytes(32, 64, nullable=True)
    }

    sql = '''
    INSERT INTO journalists (username, first_name, last_name, pw_salt, pw_hash, is_admin,
        otp_secret, is_totp, hotp_counter, last_token, created_on, last_access, passphrase_hash)
    VALUES (:username, :first_name, :last_name, :pw_salt, :pw_hash, :is_admin, :otp_secret,
        :is_totp, :hotp_counter, :last_token, :created_on, :last_access, :passphrase_hash);
    '''
    db.engine.execute(text(sql), **params)
    db.session.commit()


def add_reply(journalist_id, source_id):
    params = {
        'journalist_id': journalist_id,
        'source_id': source_id,
        'filename': random_chars(50),
        'size': random.randint(0, 1024 * 1024 * 500),
    }

    sql = '''
    INSERT INTO replies (journalist_id, source_id, filename, size)
    VALUES (:journalist_id, :source_id, :filename, :size)
    '''
    db.engine.execute(text(sql), **params)


def add_reply_after_migration(journalist_id, source_id, set_deleted_by_source):
    params = {
        'journalist_id': journalist_id,
        'source_id': source_id,
        'filename': random_chars(50),
        'size': random.randint(0, 1024 * 1024 * 500),
        'deleted_by_source': set_deleted_by_source
    }

    sql = '''
    INSERT INTO replies (journalist_id, source_id, filename, size, deleted_by_source)
    VALUES (:journalist_id, :source_id, :filename, :size, :deleted_by_source)
    '''
    db.engine.execute(text(sql), **params)


SOURCE_NUM = 200
JOURNO_NUM = 20


class UpgradeTester():

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            for _ in range(JOURNO_NUM):
                add_journalist()

            add_source()

            for jid in range(1, JOURNO_NUM):
                add_reply(jid, 1)

            db.session.commit()

    def check_upgrade(self):
        with self.app.app_context():
            journalists_sql = "SELECT * FROM journalists"
            journalists = db.engine.execute(text(journalists_sql)).fetchall()
            assert len(journalists) == JOURNO_NUM

        with self.app.app_context():
            replies_sql = "SELECT * FROM replies"
            replies = db.engine.execute(text(replies_sql)).fetchall()
            assert len(replies) == JOURNO_NUM - 1


class DowngradeTester():

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            for _ in range(JOURNO_NUM):
                add_journalist()

            add_source()

            for jid in range(1, JOURNO_NUM):
                add_reply(jid, 1, False)

            db.session.commit()

    def check_downgrade(self):
        '''
        Verify that:

        * The new journalists and replies columns exist before downgrade.
        * The deleted_by_source column is now gone, and otherwise the table has the
          expected number of rows.
        * The first_name and last_name columns are now gone, and otherwise the table
          has the expected number of rows.

        Note: Trying to access a non-existent column should produce an exception, as the column
        (should) be gone.
        '''

        # Pre-check that you can add new entries with the new columns before downgrade
        with self.app.app_context():
            add_journalist_after_migration()
            add_journalist_after_migration(False, False)
            assert len(journalists) == JOURNO_NUM + 2
            journalist_with_name_count = 0
            journalist_without_name_count = 0
            for journalist in journalists:
                if journalist.first_name is not None and journalist.last_name is not None:
                    journalist_with_name_count += 1
                elif journalist.first_name is None and journalist.last_name is None:
                    journalist_without_name_count += 1
            assert journalist_with_name_count == 1
            assert journalist_without_name_count == JOURNO_NUM + 1

            replies_sql = "SELECT * FROM replies"
            replies = db.engine.execute(text(replies_sql)).fetchall()
            assert len(replies) == JOURNO_NUM - 1
            add_reply_after_migration(1, 1, False)
            assert len(replies_sql) == JOURNO_NUM
            for reply in replies:
                assert reply.deleted_by_source is False

        with self.app.app_context():
            journalists_sql = "SELECT * FROM journalists"
            journalists = db.engine.execute(text(journalists_sql)).fetchall()
            for journalist in journalists:
                try:
                    assert journalist.uuid is not None
                except NoSuchColumnError:
                    pass

            assert len(journalists) == JOURNO_NUM

            replies_sql = "SELECT * FROM replies"
            replies = db.engine.execute(text(replies_sql)).fetchall()
            for reply in replies:
                try:
                    assert reply['deleted_by_source'] is None
                except NoSuchColumnError:
                    pass

            assert len(replies) == JOURNO_NUM - 1
