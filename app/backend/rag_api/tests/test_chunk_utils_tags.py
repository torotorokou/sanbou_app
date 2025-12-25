import pytest

from app.utils.chunk_utils import safe_parse_tags, search_documents_with_category


class DummyDoc:
    def __init__(self, page_content: str, metadata: dict):
        self.page_content = page_content
        self.metadata = metadata


class DummyVectorStore:
    def __init__(self, docs):
        # docs: list[DummyDoc]
        self._docs = docs

    def similarity_search_with_score(self, query, k=4):
        # return top-k with dummy score
        return [(d, 0.0) for d in self._docs[:k]]


@pytest.mark.parametrize(
    "raw, expected",
    [
        ([], []),
        (["A", "B"], ["A", "B"]),
        ("['A','B']", ["A", "B"]),
        ("A,B", ["A", "B"]),
        ("A", ["A"]),
        (None, []),
        (1, [1]),
    ],
)
def test_safe_parse_tags(raw, expected):
    assert safe_parse_tags(raw) == expected


@pytest.mark.parametrize(
    "meta_key",
    ["tag", "tags"],
)
def test_search_with_tag_and_tags_keys(meta_key):
    docs = [
        DummyDoc(
            page_content="doc1",
            metadata={
                "title": "t1",
                "category": ["施設"],
                meta_key: ["工場面積", "施設情報"],
            },
        ),
        DummyDoc(
            page_content="doc2",
            metadata={
                "title": "t2",
                "category": ["施設"],
                meta_key: ["別タグ"],
            },
        ),
    ]
    store = DummyVectorStore(docs)
    # query tags share one with doc1 (施設情報)
    res = search_documents_with_category(
        query="工場の面積はどれくらいですか？",
        category="施設",
        json_data=[],
        vectorstore=store,
        top_k=4,
        tags=["工場所在地", "施設情報"],
    )
    # should at least include doc1
    assert any(r[0] == "t1" for r in res)
