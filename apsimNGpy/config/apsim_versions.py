from config import apsim_version


BASE_RELEASE_NO = '2025.8.7837.0'
GITHUB_RELEASE_NO = '0.0.0.0'
try:
    APSIM_VERSION_NO = apsim_version(release_number=True)
except Exception as e:
    APSIM_VERSION_NO = None
