from src.domain.entities.upload import Upload, UploadStatus


def test_create_sets_received_status():
    upload = Upload.create(
        filename="arch.png",
        content_type="image/png",
        s3_key="uploads/some-id/arch.png",
        file_size=2048,
    )
    assert upload.status == UploadStatus.RECEIVED
    assert upload.filename == "arch.png"
    assert upload.content_type == "image/png"
    assert upload.file_size == 2048
    assert upload.id is not None
    assert upload.error_message is None
    assert upload.created_at is not None
    assert upload.updated_at is not None


def test_create_generates_unique_ids():
    u1 = Upload.create("a.png", "image/png", "s3/a.png", 100)
    u2 = Upload.create("b.png", "image/png", "s3/b.png", 200)
    assert u1.id != u2.id


def test_update_status_to_processing():
    upload = Upload.create("f.png", "image/png", "s3/f.png", 100)
    upload.update_status(UploadStatus.PROCESSING)
    assert upload.status == UploadStatus.PROCESSING
    assert upload.error_message is None


def test_update_status_to_analyzed():
    upload = Upload.create("f.png", "image/png", "s3/f.png", 100)
    upload.update_status(UploadStatus.ANALYZED)
    assert upload.status == UploadStatus.ANALYZED


def test_update_status_sets_error_message():
    upload = Upload.create("f.png", "image/png", "s3/f.png", 100)
    upload.update_status(UploadStatus.ERROR, error_message="something went wrong")
    assert upload.status == UploadStatus.ERROR
    assert upload.error_message == "something went wrong"


def test_update_status_updates_timestamp():
    upload = Upload.create("f.png", "image/png", "s3/f.png", 100)
    original_updated_at = upload.updated_at
    upload.update_status(UploadStatus.PROCESSING)
    assert upload.updated_at >= original_updated_at


def test_upload_status_str_values():
    assert UploadStatus.RECEIVED == "RECEIVED"
    assert UploadStatus.PROCESSING == "PROCESSING"
    assert UploadStatus.ANALYZED == "ANALYZED"
    assert UploadStatus.ERROR == "ERROR"
