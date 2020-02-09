import subprocess
import tempfile

from jirafs.plugin import ImageMacroPlugin, PluginValidationError, PluginOperationError
from jirafs.types import JirafsMacroAttributes


class MermaidMixin(object):
    def _get_command_args(
        self, input_filename: str, output_filename: str, theme: str = "default"
    ):
        command = [
            "mmdc",
            "-t",
            theme,
            "-i",
            input_filename,
            "-o",
            output_filename,
        ]

        return command

    def _build_output(
        self, input_filename: str, output_filename: str, theme: str = "default"
    ):
        proc = subprocess.Popen(
            self._get_command_args(input_filename, output_filename, theme=theme,),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()

        if proc.returncode:
            raise PluginOperationError(
                "%s encountered an error while compiling from %s to %s: %s"
                % (
                    self.entrypoint_name,
                    input_filename,
                    output_filename,
                    stderr.decode("utf-8"),
                )
            )

    def validate(self):
        try:
            subprocess.check_call(
                ["which", "mmdc"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        except (subprocess.CalledProcessError, IOError, OSError):
            raise PluginValidationError(
                f"{self.entrypoint_name} requires mermaid.cli (which provides the "
                f"'mmdc' command) to be installed."
            )


class Mermaid(MermaidMixin, ImageMacroPlugin):
    """ Converts mermaid markup into images using mermaid.cli"""

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"
    TAG_NAME = "mermaid"

    def get_extension_and_image_data(self, data: str, attrs: JirafsMacroAttributes):
        theme = attrs.get("theme", "default")
        format = attrs.get("format", "png")

        with tempfile.NamedTemporaryFile("w") as inf:
            inf.write(data)
            inf.flush()

            with tempfile.NamedTemporaryFile("wb+", suffix=f".{format}") as outf:
                self._build_output(
                    inf.name, outf.name, theme=theme,
                )

                outf.seek(0)
                return format, outf.read()
