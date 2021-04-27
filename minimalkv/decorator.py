from typing import Iterable
from urllib.parse import quote_plus, unquote_plus


class StoreDecorator:
    """Base class for store decorators.

    The default implementation will use :func:`getattr` to pass through all
    attribute/method requests to an underlying object stored as
    :attr:`_dstore`. It will also pass through the :attr:`__getattr__` and
    :attr:`__contains__` python special methods.

    Parameters
    ----------

    Returns
    -------

    """

    def __init__(self, store):
        """

        Parameters
        ----------
        store :


        Returns
        -------

        """
        self._dstore = store

    def __getattr__(self, attr):
        """

        Parameters
        ----------
        attr :


        Returns
        -------

        """
        store = object.__getattribute__(self, "_dstore")
        return getattr(store, attr)

    def __contains__(self, key: str) -> bool:
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        return self._dstore.__contains__(key)

    def __iter__(self) -> Iterable[str]:
        """ """
        return self._dstore.__iter__()


class KeyTransformingDecorator(StoreDecorator):
    """ """

    # currently undocumented (== not advertised as a feature)
    def _map_key(self, key: str) -> str:
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        return key

    def _map_key_prefix(self, key_prefix: str) -> str:
        """

        Parameters
        ----------
        key_prefix: str :


        Returns
        -------

        """
        return key_prefix

    def _unmap_key(self, key: str) -> str:
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        return key

    def _filter(self, key: str) -> bool:
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        return True

    def __contains__(self, key: str) -> bool:
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        return self._map_key(key) in self._dstore

    def __iter__(self) -> Iterable[str]:
        """ """
        return self.iter_keys()

    def delete(self, key: str):
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        return self._dstore.delete(self._map_key(key))

    def get(self, key, *args, **kwargs):
        """

        Parameters
        ----------
        key :

        *args :

        **kwargs :


        Returns
        -------

        """
        return self._dstore.get(self._map_key(key), *args, **kwargs)

    def get_file(self, key: str, *args, **kwargs):
        """

        Parameters
        ----------
        key: str :

        *args :

        **kwargs :


        Returns
        -------

        """
        return self._dstore.get_file(self._map_key(key), *args, **kwargs)

    def iter_keys(self, prefix: str = "") -> Iterable[str]:
        """

        Parameters
        ----------
        prefix: str :
             (Default value = "")

        Returns
        -------

        """
        return (
            self._unmap_key(k)
            for k in self._dstore.iter_keys(self._map_key_prefix(prefix))
            if self._filter(k)
        )

    def iter_prefixes(self, delimiter: str, prefix: str = "") -> Iterable[str]:
        """

        Parameters
        ----------
        delimiter: str :

        prefix: str :
             (Default value = "")

        Returns
        -------

        """
        dlen = len(delimiter)
        plen = len(prefix)
        memory = set()

        for k in self.iter_keys(prefix):
            pos = k.find(delimiter, plen)
            if pos >= 0:
                k = k[: pos + dlen]

            if k not in memory:
                yield k
                memory.add(k)

    def keys(self, prefix: str = ""):
        """Return a list of keys currently in store, in any order

        Parameters
        ----------
        prefix: str :
             (Default value = "")

        Returns
        -------

        Raises
        ------
        IOError
            If there was an error accessing the store.

        """
        return list(self.iter_keys(prefix))

    def open(self, key: str):
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        return self._dstore.open(self._map_key(key))

    def put(self, key: str, *args, **kwargs):
        """

        Parameters
        ----------
        key: str :

        *args :

        **kwargs :


        Returns
        -------

        """
        return self._unmap_key(self._dstore.put(self._map_key(key), *args, **kwargs))

    def put_file(self, key: str, *args, **kwargs):
        """

        Parameters
        ----------
        key: str :

        *args :

        **kwargs :


        Returns
        -------

        """
        return self._unmap_key(
            self._dstore.put_file(self._map_key(key), *args, **kwargs)
        )

    # support for UrlMixin
    def url_for(self, key: str, *args, **kwargs) -> str:
        """

        Parameters
        ----------
        key: str :

        *args :

        **kwargs :


        Returns
        -------

        """
        return self._dstore.url_for(self._map_key(key), *args, **kwargs)

    # support for CopyMixin
    def copy(self, source: str, dest: str):
        """

        Parameters
        ----------
        source: str :

        dest: str :


        Returns
        -------

        """
        return self._dstore.copy(self._map_key(source), self._map_key(dest))


class PrefixDecorator(KeyTransformingDecorator):
    """Prefixes any key with a string before passing it on the decorated
    store. Automatically strips the prefix upon key retrieval.

    Parameters
    ----------
    store :
        The store to pass keys on to.
    prefix :
        Prefix to add.

    Returns
    -------

    """

    def __init__(self, prefix: str, store):
        """

        Parameters
        ----------
        prefix: str :

        store :


        Returns
        -------

        """
        super(PrefixDecorator, self).__init__(store)
        self.prefix = prefix

    def _filter(self, key: str) -> bool:
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        return key.startswith(self.prefix)

    def _map_key(self, key: str) -> str:
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        self._check_valid_key(key)
        return self.prefix + key

    def _map_key_prefix(self, key_prefix: str) -> str:
        """

        Parameters
        ----------
        key_prefix: str :


        Returns
        -------

        """
        return self.prefix + key_prefix

    def _unmap_key(self, key: str) -> str:
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        assert key.startswith(self.prefix)

        return key[len(self.prefix) :]


class URLEncodeKeysDecorator(KeyTransformingDecorator):
    """URL-encodes keys before passing them on to the underlying store."""

    def _map_key(self, key: str) -> str:
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        if not isinstance(key, str):
            raise ValueError("%r is not a unicode string" % key)
        quoted = quote_plus(key.encode("utf-8"))
        if isinstance(quoted, bytes):
            quoted = quoted.decode("utf-8")
        return quoted

    def _map_key_prefix(self, key_prefix: str) -> str:
        """

        Parameters
        ----------
        key_prefix: str :


        Returns
        -------

        """
        return self._map_key(key_prefix)

    def _unmap_key(self, key: str) -> str:
        """

        Parameters
        ----------
        key: str :


        Returns
        -------

        """
        return unquote_plus(key)


class ReadOnlyDecorator(StoreDecorator):
    """A read-only view of an underlying minimalkv store

    Provides only access to the following methods/attributes of the
    underlying store: get, iter_keys, keys, open, get_file.
    It also forwards __contains__.
    Accessing any other method will raise AttributeError.

    Note that the original store for r/w can still be accessed,
    so using this class as a wrapper only provides protection
    against bugs and other kinds of unintentional writes;
    it is not meant to be a real security measure.

    Parameters
    ----------

    Returns
    -------

    """

    def __getattr__(self, attr):
        """

        Parameters
        ----------
        attr :


        Returns
        -------

        """
        if attr in ("get", "iter_keys", "keys", "open", "get_file"):
            return super(ReadOnlyDecorator, self).__getattr__(attr)
        else:
            raise AttributeError
