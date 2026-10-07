from app.adapters.storage.s3_storage import S3Storage


class StubS3:
    def __init__(self):
        self.puts, self.deletes = [], []

    def put_object(self, **kwargs):
        self.puts.append(kwargs)

    def delete_object(self, **kwargs):
        self.deletes.append(kwargs)


def make():
    client = StubS3()
    return S3Storage("my-bucket", "ap-south-1", client=client), client


def test_save_puts_the_file_under_uploads_and_returns_its_public_url():
    storage, client = make()
    url = storage.save(b"img", "abc.webp")
    assert url == "https://my-bucket.s3.ap-south-1.amazonaws.com/uploads/abc.webp"
    assert (
        client.puts[0]["Key"] == "uploads/abc.webp"
        and client.puts[0]["ContentType"] == "image/webp"
    )


def test_delete_removes_uploaded_files_and_ignores_everything_else():
    storage, client = make()
    storage.delete("https://my-bucket.s3.ap-south-1.amazonaws.com/uploads/abc.webp")
    storage.delete("/media/seed/1/0.webp")  # bundled seed image
    storage.delete("https://elsewhere.example/uploads/abc.webp")
    assert client.deletes == [{"Bucket": "my-bucket", "Key": "uploads/abc.webp"}]
