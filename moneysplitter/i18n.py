"""Translation module."""
import i18n as trans

trans.set("filename_format", "{locale}.{format}")
trans.set("skip_locale_root_data", True)
trans.set("locale", "english")
trans.set("fallback", "english")
trans.load_path.append("./translations/")

supported_languages = [
    "english",
]
