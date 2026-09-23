"""Include the canonical configuration without a second maintained YAML file."""

from pathlib import Path
import shutil

from setuptools.command.build_py import build_py


class BuildPy(build_py):
    """Ship the exact source defaults in wheels, including wheels from sdists."""

    def _defaults_output(self) -> str:
        return str(Path(self.build_lib) / "controlplane" / "default_config.yaml")

    def run(self) -> None:
        """Editable checkouts read their source config; wheels own a resource."""
        super().run()
        if self.editable_mode:
            return
        destination = self._defaults_output()
        self.mkpath(str(Path(destination).parent))
        if not self.dry_run:
            # Always copy: an incremental build must not retain obsolete defaults
            # merely because its destination has a later filesystem timestamp.
            shutil.copyfile("config.yaml", destination)

    def get_source_files(self) -> list[str]:
        """Keep the canonical file available when rebuilding a source archive."""
        return [*super().get_source_files(), "config.yaml"]

    def get_outputs(self, include_bytecode: int = 1) -> list[str]:
        """Expose the generated resource to the wheel installation command."""
        return [*super().get_outputs(include_bytecode), self._defaults_output()]

    def get_output_mapping(self) -> dict[str, str]:
        """Let editable builders link the resource to its canonical source."""
        return {**super().get_output_mapping(), self._defaults_output(): "config.yaml"}
