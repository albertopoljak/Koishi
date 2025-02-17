__all__ = ('ImageHandlerWaifuPics', )

from scarletio import IgnoreCaseMultiValueDictionary, copy_docs
from scarletio.web_common.headers import CONTENT_TYPE

from ..image_detail import ImageDetail

from .request_base import ImageHandlerRequestBase


WAIFU_API_BASE_URL = 'https://api.waifu.pics'
PROVIDER = 'waifu.pics'

HEADERS = IgnoreCaseMultiValueDictionary()
HEADERS[CONTENT_TYPE] = 'application/json'

DATA = b'{}'


class ImageHandlerWaifuPics(ImageHandlerRequestBase):
    """
    Image handler requesting images from `waifu.pics`.
    
    Attributes
    ----------
    _cache : `list` of ``ImageDetail``
        Additional requested card details.
    _waiters : `Deque` of ``Future``
        Waiter futures for card detail.
    _request_task : `None`, ``Task`` of ``._request_loop``
        Active request loop.
    _url : `str`
        The url to do request towards.
    """
    __slots__ = ('_url',)
    
    def __new__(cls, waifu_type, nsfw):
        """
        Parameters
        ----------
        waifu_type : `str`
            The waifu's type.
        nsfw : `bool`
            Ara ara.
        """
        self = ImageHandlerRequestBase.__new__(cls)
        self._url = f'{WAIFU_API_BASE_URL}/many/{"n" if nsfw else ""}sfw/{waifu_type}'
        return self
    
    
    @copy_docs(ImageHandlerRequestBase._request)
    async def _request(self, client):
        try:
            async with client.http.post(self._url, headers = HEADERS, data = DATA) as response:
                if response.status == 200:
                    data = await response.json()
                else:
                    data = None
        except TimeoutError:
            data = None
        
        return data
    
    
    @copy_docs(ImageHandlerRequestBase._process_data)
    def _process_data(self, data):
        if not isinstance(data, dict):
            return
        
        try:
            urls = data['files']
        except KeyError:
            return None
        
        return [ImageDetail(url, None, PROVIDER) for url in urls]
