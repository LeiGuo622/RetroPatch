import argparse
import logging
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir_path = os.path.join(parent_dir, "src")
sys.path.append(src_dir_path)

from backporting import load_yml
from tools.logger import logger
from tools.project import Project
from tools.utils import revise_patch


def main():
    """
    For generated patch, use this file to validate the patch if it could compile, pass test and poc.
    """
    # parse arguments
    parser = argparse.ArgumentParser(
        description="Backports patch with the help of LLM",
        usage="%(prog)s --config CONFIG.yml\ne.g.: python %(prog)s --config CVE-examaple.yml",
    )
    parser.add_argument(
        "-c", "--config", type=str, required=True, help="CVE config yml"
    )
    parser.add_argument("-d", "--debug", action="store_true", help="enable debug mode")
    args = parser.parse_args()
    debug_mode = args.debug
    config_file = args.config
    if debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Initialize: load config, create project and get sh file in dataset
    data = load_yml(config_file)
    for file in os.listdir(data.patch_dataset_dir):
        if os.path.exists(f"{data.project_dir}{file}"):
            os.remove(f"{data.project_dir}{file}")
        os.symlink(f"{data.patch_dataset_dir}{file}", f"{data.project_dir}{file}")
    project = Project(data.project_url, data.project_dir, data.patch_dataset_dir)

    # HACK: call func to test patch here, for example, I call `_validate`
    revised_patch, _ = revise_patch(patch, project.dir)
    project.all_hunks_applied_succeeded = True
    project._validate(data.target_release, revised_patch)
    if project.poc_succeeded:
        logger.info(
            f"Patch successfully passes validation on target release {data.target_release}"
        )
    else:
        logger.error(
            f"Patch failed to pass validation on target release {data.target_release}"
        )


if __name__ == "__main__":
    # HACK: put the patch here
    patch = """
--- a/tools/tiffcp.c
+++ b/tools/tiffcp.c
@@ -1490,6 +1490,13 @@
 		return 0;
 	}
+
+	if ((imagew - tilew * spp) > INT_MAX) {
+		TIFFError(TIFFFileName(in),
+		          "Error, image raster scan line size is too large");
+		return 0;
+	}
+
 	iskew = imagew - tilew*spp;
 	tilebuf = limitMalloc(tilesize);
 	if (tilebuf == 0)
"""
    main()
