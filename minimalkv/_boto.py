def _get_s3bucket(
    host,
    bucket,
    access_key,
    secret_key,
    force_bucket_suffix=True,
    create_if_missing=True,
):
    # TODO: Write docstring.
    from boto.s3.connection import S3ResponseError  # type: ignore
    from boto.s3.connection import OrdinaryCallingFormat, S3Connection

    s3con = S3Connection(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        host=host,
        is_secure=False,
        calling_format=OrdinaryCallingFormat(),
    )
    # add access key prefix to bucket name, unless explicitly prohibited
    if force_bucket_suffix and not bucket.lower().endswith("-" + access_key.lower()):
        bucket = bucket + "-" + access_key.lower()
    try:
        return s3con.get_bucket(bucket)
    except S3ResponseError as ex:
        if ex.status == 404:
            if create_if_missing:
                return s3con.create_bucket(bucket)
            else:
                raise OSError(f"Bucket {bucket} does not exist")
        raise
