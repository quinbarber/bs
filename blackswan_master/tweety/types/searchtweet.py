import time
import urllib.parse
from typing import List, Optional

from tweety.http import RequestMaker
from tweety.types.n_types import SearchFilter

from . import Excel, Tweet, deprecated


class SearchTweets(dict):
    def __init__(
        self,
        query: str,
        search_filter: SearchFilter,
        http: RequestMaker,
        pages: int = 1,
        wait_time: int = 2,
        cursor: Optional[str] = None,
    ):
        super().__init__()
        self.tweets = []
        self.cursor = cursor
        self.is_next_page = True
        self.http = http
        self.query = query
        self.search_filter: SearchFilter = search_filter
        self.pages = pages
        self.wait_time = wait_time

    @staticmethod
    def _get_entries(response: dict) -> List[dict]:
        instructions = response["data"]["search_by_raw_query"]["search_timeline"][
            "timeline"
        ]["instructions"]
        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                return instruction["entries"]

        return []

    @staticmethod
    def _get_tweet_content_key(tweet: dict):
        if str(tweet["entryId"]).split("-")[0] == "tweet":
            return [tweet["content"]["itemContent"]["tweet_results"]["result"]]

        return []

    def get_next_page(self):
        _tweets = []
        if self.is_next_page:
            response = self.http.get_search_tweets(
                self.query, search_filter=self.search_filter, cursor=self.cursor
            )
            # TODO: validate results
            # check response has a body or something?

            entries = self._get_entries(response)

            for entry in entries:
                tweets = self._get_tweet_content_key(entry)
                for tweet in tweets:
                    try:
                        parsed = Tweet(response, tweet, self.http)
                        _tweets.append(parsed)
                        # yield parsed
                    except BaseException:
                        pass

            self.is_next_page = self._get_cursor(entries)

            for tweet in _tweets:
                self.tweets.append(tweet)

            self["tweets"] = self.tweets
            self["is_next_page"] = self.is_next_page
            self["cursor"] = self.cursor

        return self, _tweets

    def generator(self):
        for page in range(1, int(self.pages) + 1):
            _, tweets = self.get_next_page()

            yield self, tweets

            if self.is_next_page and page != self.pages:
                time.sleep(self.wait_time)

    def _get_cursor(self, entries: List[dict]) -> bool:
        for entry in entries:
            if str(entry["entryId"]).split("-")[0] == "cursor":
                if entry["content"]["cursorType"] == "Bottom":
                    new_cursor = entry["content"]["value"]
                    if new_cursor == self.cursor:
                        return False

                    self.cursor = new_cursor
                    return True

        return False

    def to_xlsx(self):
        return Excel(self.tweets, urllib.parse.quote(self.query))

    def __getitem__(self, index: int) -> Tweet:
        return self.tweets[index]

    def __iter__(self):
        for __tweet in self.tweets:
            yield __tweet

    def __len__(self):
        return len(self.tweets)

    def __repr__(self):
        return f"SearchTweets(query={self.query}, search_filter={self.search_filter}, count={self.__len__()})"

    @deprecated
    def to_dict(self):
        return self.tweets
