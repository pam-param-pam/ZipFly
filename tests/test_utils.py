from collections.abc import AsyncGenerator, Generator


lorem_ipsum = b"""Est magni commodi voluptate consequuntur qui consequatur.
Nam quaerat velit eum non autem laborum quae qui.
Maxime similique qui et natus qui ut ut et.
Quia omnis dignissimos id molestias dolores provident quis quia.
Dicta quaerat facere molestiae. Et quod totam nihil.
Repudiandae enim esse optio ut nostrum aliquam et cumque.
Distinctio molestiae dolore et debitis saepe optio.
Incidunt id quo rerum dicta dolorem.
Eos non eum qui totam.
Dolores laborum quibusdam fugiat temporibus sed quia voluptatem dolor.
Fugit ut iste voluptatem dolores et vero.
Qui quibusdam nulla distinctio.
Numquam explicabo laboriosam delectus nemo recusandae blanditiis voluptates.
Esse ea magnam qui ea.
Id quo odio saepe rerum quia natus odio exercitationem.
Deleniti sunt dolores cupiditate quia eum ab fugit.
Similique ullam et tempore sunt incidunt ipsa.
Molestiae est harum similique aspernatur distinctio aut."""

single_archive_size = 1152
single_archive_size_with_extra_field = 1172
multifile_archive_size = 5388


def lorem_ipsum_generator() -> Generator[bytes]:
    """Yield lines of lorem ipsum."""
    lines = lorem_ipsum.split(b"\n")
    # Don't yield trailing newline
    for line in lines[:-1]:
        yield line
        yield b"\n"
    yield lines[-1]


async def lorem_ipsum_generator_async() -> AsyncGenerator[bytes]:
    """Yield lines of lorem ipsum."""
    for line in lorem_ipsum_generator():
        yield line


def sized_zeros_generator(size: int) -> Generator[bytes]:
    """Yield zeros up to a certain size."""
    yielded = 0
    line = b"0" * 1024
    while yielded < size:
        yield line[: size - yielded]
        yielded += len(line[: size - yielded])
        if yielded >= size:
            break


async def sized_zeros_generator_async(size: int) -> AsyncGenerator[bytes]:
    """Yield zeros up to a certain size."""
    for zeros in sized_zeros_generator(size):
        yield zeros

def generate_data_async(data: bytes, repeat: int):
    async def generator():
        for _ in range(repeat):
            yield data
    return generator
