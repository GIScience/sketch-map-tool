import psycopg2


def bytea2bytes(value, cur):
    """Cast memoryview to binary."""
    m = psycopg2.BINARY(value, cur)
    if m is not None:
        return m.tobytes()


# psycopg2 returns memoryview when reading blobs from DB. We need binary since
# memoryview can not be pickled which is a requirement for result of a celery task.
BYTEA2BYTES = psycopg2.extensions.new_type(
    psycopg2.BINARY.values, "BYTEA2BYTES", bytea2bytes
)
psycopg2.extensions.register_type(BYTEA2BYTES)
