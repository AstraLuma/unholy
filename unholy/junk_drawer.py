import io
import tarfile

def tarfile_add(tf: tarfile.TarFile, name: str, contents: str | bytes, **props):
    """
    Utility to add a file to a tarfile
    """
    if isinstance(contents, str):
        contents = contents.encode('utf-8')
    # TODO: Ensure all the directory entries exist
    ti = tarfile.TarInfo(name)
    ti.type = tarfile.REGTYPE
    ti.size = len(contents)
    for k, v in props.items():
        setattr(ti, k, v)

    tf.addfile(ti, io.BytesIO(contents))
