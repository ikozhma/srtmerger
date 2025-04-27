from pathlib import Path
from typing import Optional

import click

from srtmerger_cli.main import Colors, Merger
from loguru import logger


SUB_ARG_TYPE = click.Path(exists=True, dir_okay=False, path_type=Path)
OUTPUT_PATH_TYPE = click.Path(exists=False, path_type=Path)


@click.command(help="Supports only .srt subs")
@click.argument("upper_sub", type=SUB_ARG_TYPE)  # cls=Path)
@click.argument("lower_sub", type=SUB_ARG_TYPE)  # , cls=Path)
@click.option("--upper_yellow", is_flag=True, help="Make upper sub yellow")
@click.option("--lower_yellow", is_flag=True, help="Make lower sub yellow")
@click.option("--top", is_flag=True,help="Place upper subs on top")
@click.option(
    "--output",
    type=OUTPUT_PATH_TYPE,
    help="Path of the output file or folder. Default= folder of the upper_sub / '{upper_sub.stem}_{lower_sub.stem}_merged.srt'",
)
def merge_subs(
    upper_sub: Path, lower_sub: Path, *, upper_yellow: bool = False, lower_yellow: bool = False, output: Optional[Path] = None, top : bool = False
) -> None:
    if {sub.suffix for sub in (upper_sub, lower_sub)} != {".srt"}:
        raise NotImplementedError("Script supports only .srt subs")
    merged_sub_name = f"{upper_sub.stem}_{lower_sub.stem}_merged.srt"

    if output:
        if output.is_dir():
            m = Merger(output_path=str(output), output_name=merged_sub_name)
        else:
            m = Merger(output_path=str(output.parent), output_name=output.name)
    else:
        m = Merger(output_name=merged_sub_name)
    logger.info("Reading upper_sub")
    m.add(str(upper_sub), color=Colors.YELLOW if upper_yellow else Colors.WHITE, top=top)
    logger.info("Reading lower_sub")
    m.add(str(lower_sub), color=Colors.YELLOW if lower_yellow else Colors.WHITE)
    # m.add('./test_srt/fa.srt', color="yellow", codec="cp1256", top=True)
    m.merge()


# click.Option()


if __name__ == "__main__":
    pass