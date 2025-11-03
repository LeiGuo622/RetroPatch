import argparse
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir_path = os.path.join(parent_dir, "src")
sys.path.append(src_dir_path)

from do_one_fix import load_yml
from tools.logger import logger
from tools.project import Project
from tools.utils import revise_patch


def main():
    """
    For generated patch, use this file to validate the patch if it could compile, pass test and poc.
    """
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

    data = load_yml(config_file)

    data.project_dir = os.path.expanduser(
        data.project_dir if data.project_dir.endswith("/") else data.project_dir + "/"
    )
    data.patch_dataset_dir = os.path.expanduser(
        data.patch_dataset_dir
        if data.patch_dataset_dir.endswith("/")
        else data.patch_dataset_dir + "/"
    )

    if not os.path.isdir(data.project_dir):
        logger.error(f"Project directory does not exist: {data.project_dir}")
        exit(1)
    if not os.path.isdir(data.patch_dataset_dir):
        logger.error(
            f"Patch dataset directory does not exist: {data.patch_dataset_dir}"
        )
        exit(1)

    project = Project(data.project_url, data.project_dir, data.patch_dataset_dir)
    revised_patch, _ = revise_patch(patch, project.dir)
    project.all_hunks_applied_succeeded = True
    project._validate(data.target_release, revised_patch)
    if project.poc_succeeded:
        logger.info(
            f"Patch successfully passes validation on target release {data.target_release}"
        )


if __name__ == "__main__":
    # put the patch here
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
