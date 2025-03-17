"""Custom Exceptions for Allep Installer."""

class PackageExtractionError(Exception):
    """Error raised during Package Extraction."""

class InstallRequirementsError(Exception):
    """Error raised during requirements installation."""

class CreateActionBarError(Exception):
    """Error raised during creating actb and npd file."""

class MinimumAllplanVersionError(Exception):
    """Error raised when current version is less than minimum versions specified
       The minimum version is specified  in the install config.
    """

class AbortInstallError(Exception):
    """Error raised when installation needs to be aborted
    """
