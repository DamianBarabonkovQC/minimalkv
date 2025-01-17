from functools import reduce
from typing import Any

from minimalkv._key_value_store import KeyValueStore
from minimalkv._urls import url2dict


def get_store_from_url(url: str) -> KeyValueStore:
    """
    Take a URL and return a minimalkv store according to the parameters in the URL.

    Parameters
    ----------
    url : str
        Access-URL, see below for supported formats.

    Returns
    -------
    store : KeyValueStore
        Value Store as described in url.

    Notes
    -----
    User credentials like secret keys have to be percent-encoded before they can be used
    in a URL (see ``azure`` and ``s3`` store types), since they can contain characters
    that are not valid in this part of a URL, like forward-slashes.

    You can use Python to percent-encode your secret key on the commandline like so::

        $ python -c "import urllib; print urllib.quote_plus('''dead/beef''')"
        dead%2Fbeef

    Store types and URL forms:

        * DictStore: ``memory://``
        * RedisStore: ``redis://[[password@]host[:port]][/db]``
        * FilesystemStore: ``fs://path``
        * BotoStore ``s3://access_key:secret_key@endpoint/bucket[?create_if_missing=true]``
        * AzureBlockBlockStorage: ``azure://account_name:account_key@container[?create_if_missing=true]``
        * AzureBlockBlockStorage (SAS): ``azure://account_name:shared_access_signature@container?use_sas&create_if_missing=false``
        * AzureBlockBlockStorage (SAS): ``azure://account_name:shared_access_signature@container?use_sas&create_if_missing=false[?max_connections=2&socket_timeout=(20,100)]``
        * AzureBlockBlockStorage (SAS): ``azure://account_name:shared_access_signature@container?use_sas&create_if_missing=false[?max_connections=2&socket_timeout=(20,100)][?max_block_size=4*1024*1024&max_single_put_size=64*1024*1024]``
        * GoogleCloudStorage: ``gcs://<base64 encoded credentials JSON>@bucket_name[?create_if_missing=true][&bucket_creation_location=EUROPE-WEST1]``

    Get the encoded credentials as string like so:

    .. code-block:: python

    from pathlib import Path
    import base64
    json_as_bytes = Path(<path_to_json>).read_bytes()
    json_b64_encoded = base64.urlsafe_b64encode(b).decode()

    """
    return get_store(**url2dict(url))


def get_store(
    type: str, create_if_missing: bool = True, **params: Any
) -> KeyValueStore:
    """Return a storage object according to the ``type`` and additional parameters.

    The ``type`` must be one of the types below, where each allows requires different
    parameters:

    * ``"azure"``: Returns a ``minimalkv.azure.AzureBlockBlobStorage``. Parameters are
      ``"account_name"``, ``"account_key"``, ``"container"``, ``"use_sas"`` and ``"create_if_missing"`` (default: ``True``).
      ``"create_if_missing"`` has to be ``False`` if ``"use_sas"`` is set. When ``"use_sas"`` is set,
      ``"account_key"`` is interpreted as Shared Access Signature (SAS) token.FIRE
      ``"max_connections"``: Maximum number of network connections used by one store (default: ``2``).
      ``"socket_timeout"``: maximum timeout value in seconds (socket_timeout: ``200``).
      ``"max_single_put_size"``: max_single_put_size is the largest size upload supported in a single put call.
      ``"max_block_size"``: maximum block size is maximum size of the blocks(maximum size is <= 100MB)
    * ``"s3"``: Returns a plain ``minimalkv.net.botostore.BotoStore``.
      Parameters must include ``"host"``, ``"bucket"``, ``"access_key"``, ``"secret_key"``.
      Optional parameters are

       - ``"force_bucket_suffix"`` (default: ``True``). If set, it is ensured that
         the bucket name ends with ``-<access_key>``
         by appending this string if necessary;
         If ``False``, the bucket name is used as-is.
       - ``"create_if_missing"`` (default: ``True`` ). If set, creates the bucket if it does not exist;
         otherwise, try to retrieve the bucket and fail with an ``IOError``.
    * ``"hs3"`` returns a variant of ``minimalkv.net.botostore.BotoStore`` that allows "/" in the key name.
      The parameters are the same as for ``"s3"``
    * ``"gcs"``: Returns a ``minimalkv.net.gcstore.GoogleCloudStore``.  Parameters are
      ``"credentials"``, ``"bucket_name"``, ``"bucket_creation_location"``, ``"project"`` and ``"create_if_missing"`` (default: ``True``).

      - ``"credentials"``: either the path to a credentials.json file or a *google.auth.credentials.Credentials* object
      - ``"bucket_name"``: Name of the bucket the blobs are stored in.
      - ``"project"``: The name of the GCStorage project. If a credentials JSON is passed then it contains the project name
        and this parameter will be ignored.
      - ``"create_if_missing"``: [optional] Create new bucket to store blobs in if ``"bucket_name"`` doesn't exist yet. (default: ``True``).
      - ``"bucket_creation_location"``: [optional] If a new bucket is created (create_if_missing=True), the location it will be created in.
        If ``None`` then GCloud uses a default location.
    * ``"hgcs"``: Like ``"gcs"`` but "/" are allowed in the keynames.
    * ``"fs"``: Returns a ``minimalkv.fs.FilesystemStore``. Specify the base path as "path" parameter.
    * ``"hfs"`` returns a variant of ``minimalkv.fs.FilesystemStore``  that allows "/" in the key name.
      The parameters are the same as for ``"file"``.
    * ``"memory"``: Returns a DictStore. Doesn't take any parameters
    * ``"redis"``: Returns a RedisStore. Constructs a StrictRedis using params as kwargs.
      See StrictRedis documentation for details.

    Parameters
    ----------
    type : str
        Type of storage to open, with optional storage decorators.
    create_if_missing : bool, optional, default = True
        Create the "root" of the storage (Azure container, parent directory, S3 bucket,
        etc.). Has no effect for stores where this makes no sense, like ``redis`` or
        ``memory``.
    kwargs
        Parameters specific to the store type.

    Returns
    -------
    store: KeyValueStore
        Key value store of type ``type`` as described in ``kwargs`` parameters.

    """
    from minimalkv._store_creation import create_store
    from minimalkv._store_decoration import decorate_store

    # split off old-style wrappers, if any:
    parts = type.split("+")
    type = parts.pop(-1)
    decorators = list(reversed(parts))

    # find new-style wrappers, if any:
    wrapspec = params.pop("wrap", "")
    wrappers = list(wrapspec.split("+")) if wrapspec else []

    # can't have both:
    if wrappers:
        if decorators:
            raise ValueError(
                "Adding store wrappers via store type as well as via wrap parameter are not allowed. Preferably use wrap."
            )
        decorators = wrappers

    # create_if_missing is a universal parameter, so it's part of the function signature
    # it can be safely ignored by stores where 'creating' makes no sense.
    params["create_if_missing"] = create_if_missing

    store = create_store(type, params)

    # apply wrappers/decorators:
    wrapped_store = reduce(decorate_store, decorators, store)

    return wrapped_store
