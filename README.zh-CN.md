[![English](https://img.shields.io/badge/Lang-English-blue.svg)](README.md)

# patch-backporting

## 演示

[![asciicast](https://asciinema.org/a/8J9k0iBJ6IkdDmvr.svg)](https://asciinema.org/a/8J9k0iBJ6IkdDmvr)

## 使用方法

```shell
cd src
python do_on_fix.py --config example.yml # 记得先填写配置文件。
```

## Docker 使用方法

构建 Docker 镜像：

```shell
docker build -t patch-backporting .
```

运行容器：

```shell
# 请确保挂载了必要的目录（代码、配置文件、数据集）
# 示例：假设 config.yml 位于当前目录，数据集位于 /data
docker run --rm -v $(pwd):/app/src -v /path/to/dataset:/path/to/dataset patch-backporting python backporting.py --config config.yml
```

或者，也可以使用交互模式在容器内执行脚本：

```shell
docker run --rm -it -v $(pwd):/app/src -v /path/to/dataset:/path/to/dataset patch-backporting /bin/bash
# 在容器内部执行
python backporting.py --config config.yml
```

## 配置结构

```yml
project: libtiff
project_url: https://github.com/libsdl-org/libtiff
new_patch: 881a070194783561fd209b7c789a4e75566f7f37 # 新版本中的补丁提交 ID，版本 A（已修复）
new_patch_parent: 6bb0f1171adfcccde2cd7931e74317cccb7db845 # 补丁的父提交，版本 A
target_release: 13f294c3d7837d630b3e9b08089752bc07b730e6 # 需要修复的提交 ID，版本 B
sanitizer: LeakSanitizer # poc 的 sanitizer 类型，可以为空
error_message: "ERROR: LeakSanitizer" # poc 的触发信息，可以为空
tag: CVE-2023-3576
openai_key: # 你的 OpenAI key
project_dir: dataset/libsdl-org/libtiff # 项目路径
patch_dataset_dir: ~/backports/patch_dataset/libtiff/CVE-2023-3576/ # 补丁集路径，包含 build.sh、test.sh 等文件

# 可选：Azure OpenAI 配置
# use_azure: true
# azure_endpoint: "https://your-resource.openai.azure.com/"
# azure_deployment: "gpt-4"
# azure_api_version: "2024-12-01-preview"

#                    Version A           Version A(Fixed)
#   ┌───┐            ┌───┐             ┌───┐
#   │   ├───────────►│   ├────────────►│   │
#   └─┬─┘            └───┘             └───┘
#     │
#     │
#     │
#     │              Version B
#     │              ┌───┐
#     └─────────────►│   ├────────────► ??
#                    └───┘
```
