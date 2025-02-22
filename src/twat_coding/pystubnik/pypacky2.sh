#!/usr/bin/env bash
dir=${0%/*}
if [ "$dir" = "$0" ]; then dir="."; fi
dir=$(grealpath "$dir")
cd "$dir"
workdir=$(grealpath "$dir/work")
cd "$workdir"

PROJ="sluglet"

uv venv --allow-existing --relocatable --python-preference only-system "$dir/venv" # && source work/myvenv/bin/activate
uv venv --allow-existing --relocatable --python-preference only-system "$dir/devenv"

source "$dir/devenv/bin/activate"

uv pip install -U -r "$workdir/dev_requirements.txt"

projdir=$(grealpath "$workdir/$PROJ")

UPROJ=$(echo "$PROJ" | tr '-' '_')
putup --name $UPROJ --package $UPROJ --url https://github.com/twardoch/$PROJ --license Apache-2.0 --description "Python tool to composite two images using multiple mask images" --github-actions $PROJ && cd "$projdir" && pre-commit autoupdate

cd "$projdir"
pre-commit autoupdate
rm "src/$PROJ/skeleton.py"
cp "$workdir/$PROJ.py" "$projdir/src/$PROJ/"

cd "$workdir"
pyodide minify "$PROJ"
MINIFIED_DIR="${PROJ}_stripped"
OUT_DIR="$workdir/_vulture"
mkdir -p "$OUT_DIR"
vulture "$MINIFIED_DIR" --sort-by-size --make-whitelist >"$OUT_DIR/vulture_dead_code.txt"
uv pip install -U "$projdir"

compile_with_nuitka() {
    echo "Compiling with Nuitka..."
    OUT_DIR="$workdir/_nuit"
    mkdir -p "$OUT_DIR"
    MAIN_FILE="$workdir/main.py"
    if [ -n "$MAIN_FILE" ]; then
        nuitka --standalone "$MAIN_FILE" --include-package="$PROJ" --show-modules --show-scons --output-dir="$OUT_DIR" --follow-imports --prefer-source-code
    else
        echo "Main file not found. Skipping Nuitka compilation."
    fi
}
compile_with_nuitka

package_with_pyinstaller() {
    echo "Packaging with PyInstaller..."
    OUT_DIR="$workdir/_pyins"
    mkdir -p "$OUT_DIR"
    MAIN_FILE="$workdir/main.py"
    if [ -n "$MAIN_FILE" ]; then
        pyinstaller --console --onedir -y --workpath "$OUT_DIR/work" --distpath "$OUT_DIR/dist" --specpath "$OUT_DIR/spec" "$MAIN_FILE" -d all --clean --contents-directory . --optimize 0
    else
        echo "Main file not found. Skipping PyInstaller packaging."
    fi
}
package_with_pyinstaller
