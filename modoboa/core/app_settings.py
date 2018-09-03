# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import collections

from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.lib import fields as lib_fields
from modoboa.lib.form_utils import (
    HorizontalRadioSelect, SeparatorField, YesNoField
)
from modoboa.parameters import forms as param_forms, tools as param_tools
from . import constants


def enabled_applications():
    """Return the list of installed extensions."""
    from modoboa.core.extensions import exts_pool

    result = [("user", _("User profile"))]
    for extension in exts_pool.list_all():
        if "topredirection_url" not in extension:
            continue
        result.append((extension["name"], extension["label"]))
    return sorted(result, key=lambda e: e[0])


class GeneralParametersForm(param_forms.AdminParametersForm):
    """General parameters."""

    app = "core"

    sep1 = SeparatorField(label=ugettext_lazy("Authentication"))

    authentication_type = forms.ChoiceField(
        label=ugettext_lazy("Authentication type"),
        choices=[("local", ugettext_lazy("Local")),
                 ("ldap", "LDAP")],
        initial="local",
        help_text=ugettext_lazy("The backend used for authentication"),
        widget=HorizontalRadioSelect()
    )

    password_scheme = forms.ChoiceField(
        label=ugettext_lazy("Default password scheme"),
        choices=[("sha512crypt", "sha512crypt"),
                 ("sha256crypt", "sha256crypt"),
                 ("blfcrypt", "bcrypt"),
                 ("md5crypt", ugettext_lazy("md5crypt (weak)")),
                 ("sha256", ugettext_lazy("sha256 (weak)")),
                 ("md5", ugettext_lazy("md5 (weak)")),
                 ("crypt", ugettext_lazy("crypt (weak)")),
                 ("plain", ugettext_lazy("plain (weak)"))],
        initial="sha512crypt",
        help_text=ugettext_lazy("Scheme used to crypt mailbox passwords"),
        widget=forms.Select(attrs={"class": "form-control"})
    )

    rounds_number = forms.IntegerField(
        label=ugettext_lazy("Rounds"),
        initial=70000,
        help_text=ugettext_lazy(
            "Number of rounds to use (only used by sha256crypt and "
            "sha512crypt). Must be between 1000 and 999999999, inclusive."
        ),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    default_password = forms.CharField(
        label=ugettext_lazy("Default password"),
        initial="password",
        help_text=ugettext_lazy(
            "Default password for automatically created accounts.")
    )

    random_password_length = forms.IntegerField(
        label=ugettext_lazy("Random password length"),
        min_value=8,
        initial=8,
        help_text=ugettext_lazy(
            "Length of randomly generated passwords.")
    )

    # LDAP specific settings
    ldap_sep = SeparatorField(label=ugettext_lazy("LDAP settings"))

    ldap_server_address = forms.CharField(
        label=ugettext_lazy("Server address"),
        initial="localhost",
        help_text=ugettext_lazy(
            "The IP address or the DNS name of the LDAP server"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    ldap_server_port = forms.IntegerField(
        label=ugettext_lazy("Server port"),
        initial=389,
        help_text=ugettext_lazy("The TCP port number used by the LDAP server"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    ldap_secured = forms.ChoiceField(
        label=ugettext_lazy("Use a secured connection"),
        choices=constants.LDAP_SECURE_MODES,
        initial="none",
        help_text=ugettext_lazy(
            "Use an SSL/STARTTLS connection to access the LDAP server")
    )

    ldap_auth_method = forms.ChoiceField(
        label=ugettext_lazy("Authentication method"),
        choices=[("searchbind", ugettext_lazy("Search and bind")),
                 ("directbind", ugettext_lazy("Direct bind"))],
        initial="searchbind",
        help_text=ugettext_lazy("Choose the authentication method to use"),
        widget=forms.Select(attrs={"class": "form-control"})
    )

    ldap_bind_dn = forms.CharField(
        label=ugettext_lazy("Bind DN"),
        initial="",
        help_text=ugettext_lazy(
            "The distinguished name to use when binding to the LDAP server. "
            "Leave empty for an anonymous bind"
        ),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    ldap_bind_password = forms.CharField(
        label=ugettext_lazy("Bind password"),
        initial="",
        help_text=ugettext_lazy(
            "The password to use when binding to the LDAP server "
            "(with 'Bind DN')"
        ),
        widget=forms.PasswordInput(
            attrs={"class": "form-control"}, render_value=True),
        required=False
    )

    ldap_search_base = forms.CharField(
        label=ugettext_lazy("Users search base"),
        initial="",
        help_text=ugettext_lazy(
            "The distinguished name of the search base used to find users"
        ),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    ldap_search_filter = forms.CharField(
        label=ugettext_lazy("Search filter"),
        initial="(mail=%(user)s)",
        help_text=ugettext_lazy(
            "An optional filter string (e.g. '(objectClass=person)'). "
            "In order to be valid, it must be enclosed in parentheses."
        ),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    ldap_user_dn_template = forms.CharField(
        label=ugettext_lazy("User DN template"),
        initial="",
        help_text=ugettext_lazy(
            "The template used to construct a user's DN. It should contain "
            "one placeholder (ie. %(user)s)"
        ),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    ldap_password_attribute = forms.CharField(
        label=ugettext_lazy("Password attribute"),
        initial="userPassword",
        help_text=ugettext_lazy("The attribute used to store user passwords"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    ldap_is_active_directory = YesNoField(
        label=ugettext_lazy("Active Directory"),
        initial=False,
        help_text=ugettext_lazy(
            "Tell if the LDAP server is an Active Directory one")
    )

    ldap_admin_groups = forms.CharField(
        label=ugettext_lazy("Administrator groups"),
        initial="",
        help_text=ugettext_lazy(
            "Members of those LDAP Posix groups will be created as domain "
            "administrators. Use ';' characters to separate groups."
        ),
        required=False
    )

    ldap_group_type = forms.ChoiceField(
        label=ugettext_lazy("Group type"),
        initial="posixgroup",
        choices=constants.LDAP_GROUP_TYPES,
        help_text=ugettext_lazy(
            "The LDAP group type to use with your directory."
        )
    )

    ldap_groups_search_base = forms.CharField(
        label=ugettext_lazy("Groups search base"),
        initial="",
        help_text=ugettext_lazy(
            "The distinguished name of the search base used to find groups"
        ),
        required=False
    )

    dash_sep = SeparatorField(label=ugettext_lazy("Dashboard"))

    rss_feed_url = forms.URLField(
        label=ugettext_lazy("Custom RSS feed"),
        required=False,
        help_text=ugettext_lazy(
            "Display custom RSS feed to resellers and domain administrators"
        )
    )

    hide_features_widget = YesNoField(
        label=ugettext_lazy("Hide features widget"),
        initial=False,
        help_text=ugettext_lazy(
            "Hide features widget for resellers and domain administrators"
        )
    )

    notif_sep = SeparatorField(label=ugettext_lazy("Notifications"))

    sender_address = lib_fields.UTF8EmailField(
        label=_("Sender address"),
        initial="noreply@yourdomain.test",
        help_text=_(
            "Email address used to send notifications."
        )
    )

    api_sep = SeparatorField(label=ugettext_lazy("Public API"))

    enable_api_communication = YesNoField(
        label=ugettext_lazy("Enable communication"),
        initial=True,
        help_text=ugettext_lazy(
            "Enable communication with Modoboa public API")
    )

    check_new_versions = YesNoField(
        label=ugettext_lazy("Check new versions"),
        initial=True,
        help_text=ugettext_lazy(
            "Automatically checks if a newer version is available")
    )

    send_statistics = YesNoField(
        label=ugettext_lazy("Send statistics"),
        initial=True,
        help_text=ugettext_lazy(
            "Send statistics to Modoboa public API "
            "(counters and used extensions)")
    )

    sep3 = SeparatorField(label=ugettext_lazy("Miscellaneous"))

    inactive_account_threshold = forms.IntegerField(
        label=_("Inactive account threshold"),
        initial=30,
        help_text=_(
            "An account with a last login date greater than this threshold "
            "(in days) will be considered as inactive"
        ),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    top_notifications_check_interval = forms.IntegerField(
        label=_("Top notifications check interval"),
        initial=30,
        help_text=_(
            "Interval between two top notification checks (in seconds)"
        ),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    log_maximum_age = forms.IntegerField(
        label=ugettext_lazy("Maximum log record age"),
        initial=365,
        help_text=ugettext_lazy("The maximum age in days of a log record"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    items_per_page = forms.IntegerField(
        label=ugettext_lazy("Items per page"),
        initial=30,
        help_text=ugettext_lazy("Number of displayed items per page"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    default_top_redirection = forms.ChoiceField(
        label=ugettext_lazy("Default top redirection"),
        choices=[],
        initial="user",
        help_text=ugettext_lazy(
            "The default redirection used when no application is specified"
        ),
        widget=forms.Select(attrs={"class": "form-control"})
    )

    # Visibility rules
    visibility_rules = {
        "ldap_sep": "authentication_type=ldap",
        "ldap_server_address": "authentication_type=ldap",
        "ldap_server_port": "authentication_type=ldap",
        "ldap_secured": "authentication_type=ldap",
        "ldap_auth_method": "authentication_type=ldap",
        "ldap_bind_dn": "ldap_auth_method=searchbind",
        "ldap_bind_password": "ldap_auth_method=searchbind",
        "ldap_search_base": "ldap_auth_method=searchbind",
        "ldap_search_filter": "ldap_auth_method=searchbind",
        "ldap_user_dn_template": "ldap_auth_method=directbind",
        "ldap_password_attribute": "authentication_type=ldap",
        "ldap_is_active_directory": "authentication_type=ldap",
        "ldap_admin_groups": "authentication_type=ldap",
        "ldap_group_type": "authentication_type=ldap",
        "ldap_groups_search_base": "authentication_type=ldap",
        "check_new_versions": "enable_api_communication=True",
        "send_statistics": "enable_api_communication=True",
    }

    def __init__(self, *args, **kwargs):
        super(GeneralParametersForm, self).__init__(*args, **kwargs)
        self.fields["default_top_redirection"].choices = enabled_applications()

    def clean_ldap_user_dn_template(self):
        tpl = self.cleaned_data["ldap_user_dn_template"]
        try:
            tpl % {"user": "toto"}
        except (KeyError, ValueError):
            raise forms.ValidationError(_("Invalid syntax"))
        return tpl

    def clean_rounds_number(self):
        value = self.cleaned_data["rounds_number"]
        if value < 1000 or value > 999999999:
            raise forms.ValidationError(_("Invalid rounds number"))
        return value

    def clean_default_password(self):
        """Check password complexity."""
        value = self.cleaned_data["default_password"]
        password_validation.validate_password(value)
        return value

    def clean(self):
        """Custom validation method

        Depending on 'ldap_auth_method' value, we check for different
        required parameters.
        """
        super(GeneralParametersForm, self).clean()
        cleaned_data = self.cleaned_data
        if cleaned_data["authentication_type"] != "ldap":
            return cleaned_data

        if cleaned_data["ldap_auth_method"] == "searchbind":
            required_fields = ["ldap_search_base", "ldap_search_filter"]
        else:
            required_fields = ["ldap_user_dn_template"]

        for f in required_fields:
            if f not in cleaned_data or cleaned_data[f] == u'':
                self.add_error(f, _("This field is required"))

        return cleaned_data

    def to_django_settings(self):
        """Apply LDAP related parameters to Django settings.

        Doing so, we can use the django_auth_ldap module.
        """
        try:
            import ldap
            from django_auth_ldap.config import (
                LDAPSearch, PosixGroupType, GroupOfNamesType)
            ldap_available = True
        except ImportError:
            ldap_available = False

        values = dict(param_tools.get_global_parameters("core"))
        if not ldap_available or values["authentication_type"] != "ldap":
            return
        if not hasattr(settings, "AUTH_LDAP_USER_ATTR_MAP"):
            setattr(settings, "AUTH_LDAP_USER_ATTR_MAP", {
                "first_name": "givenName",
                "email": "mail",
                "last_name": "sn"
            })
        ldap_uri = "ldaps://" if values["ldap_secured"] == "ssl" else "ldap://"
        ldap_uri += "%s:%s" % (
            values["ldap_server_address"], values["ldap_server_port"])
        setattr(settings, "AUTH_LDAP_SERVER_URI", ldap_uri)
        if values["ldap_secured"] == "starttls":
            setattr(settings, "AUTH_LDAP_START_TLS", True)

        if values["ldap_group_type"] == "groupofnames":
            setattr(settings, "AUTH_LDAP_GROUP_TYPE", GroupOfNamesType())
            searchfilter = "(objectClass=groupOfNames)"
        else:
            setattr(settings, "AUTH_LDAP_GROUP_TYPE", PosixGroupType())
            searchfilter = "(objectClass=posixGroup)"
        setattr(settings, "AUTH_LDAP_GROUP_SEARCH", LDAPSearch(
            values["ldap_groups_search_base"], ldap.SCOPE_SUBTREE,
            searchfilter
        ))
        if values["ldap_auth_method"] == "searchbind":
            setattr(settings, "AUTH_LDAP_BIND_DN", values["ldap_bind_dn"])
            setattr(
                settings, "AUTH_LDAP_BIND_PASSWORD",
                values["ldap_bind_password"]
            )
            search = LDAPSearch(
                values["ldap_search_base"], ldap.SCOPE_SUBTREE,
                values["ldap_search_filter"]
            )
            setattr(settings, "AUTH_LDAP_USER_SEARCH", search)
        else:
            setattr(
                settings, "AUTH_LDAP_USER_DN_TEMPLATE",
                values["ldap_user_dn_template"]
            )
        if values["ldap_is_active_directory"]:
            if not hasattr(settings, "AUTH_LDAP_GLOBAL_OPTIONS"):
                setattr(settings, "AUTH_LDAP_GLOBAL_OPTIONS", {
                    ldap.OPT_REFERRALS: False
                })
            else:
                settings.AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_REFERRALS] = False


GLOBAL_PARAMETERS_STRUCT = collections.OrderedDict([
    ("authentication", {
        "label": ugettext_lazy("Authentication"),
        "params": collections.OrderedDict([
            ("authentication_type", {
                "label": ugettext_lazy("Authentication type"),
                "help_text": ugettext_lazy(
                    "The backend used for authentication"),
            }),
            ("password_scheme", {
                "label": ugettext_lazy("Default password scheme"),
                "help_text": ugettext_lazy(
                    "Scheme used to crypt mailbox passwords"),
            }),
            ("rounds_number", {
                "label": ugettext_lazy("Rounds"),
                "help_text": ugettext_lazy(
                    "Number of rounds to use (only used by sha256crypt and "
                    "sha512crypt). Must be between 1000 and 999999999, "
                    "inclusive."
                )
            }),
            ("default_password", {
                "label": ugettext_lazy("Default password"),
                "help_text": ugettext_lazy(
                    "Default password for automatically created accounts.")
            }),
            ("random_password_length", {
                "label": ugettext_lazy("Random password length"),
                "help_text": ugettext_lazy(
                    "Length of randomly generated passwords.")
            })
        ])
    }),
    ("ldap", {
        "label": _("LDAP"),
        "display": "authentication_type=ldap",
        "params": collections.OrderedDict([
            ("ldap_server_address", {
                "label": ugettext_lazy("Server address"),
                "help_text": ugettext_lazy(
                    "The IP address or the DNS name of the LDAP server"),
            }),
            ("ldap_server_port", {
                "label": ugettext_lazy("Server port"),
                "help_text": ugettext_lazy(
                    "The TCP port number used by the LDAP server")
            }),
            ("ldap_secured", {
                "label": ugettext_lazy("Use a secured connection"),
                "help_text": ugettext_lazy(
                    "Use an SSL/STARTTLS connection to access the LDAP server")
            }),
            ("ldap_auth_method", {
                "label": ugettext_lazy("Authentication method"),
                "help_text": ugettext_lazy(
                    "Choose the authentication method to use"),
            }),
            ("ldap_bind_dn", {
                "label": ugettext_lazy("Bind DN"),
                "help_text": ugettext_lazy(
                    "The distinguished name to use when binding to the LDAP "
                    "server. Leave empty for an anonymous bind"
                ),
                "display": "ldap_auth_method=searchbind"
            }),
            ("ldap_bind_password", {
                "label": ugettext_lazy("Bind password"),
                "help_text": ugettext_lazy(
                    "The password to use when binding to the LDAP server "
                    "(with 'Bind DN')"
                ),
                "display": "ldap_auth_method=searchbind"
            }),
            ("ldap_search_base", {
                "label": ugettext_lazy("Users search base"),
                "help_text": ugettext_lazy(
                    "The distinguished name of the search base used to find "
                    "users"
                ),
                "display": "ldap_auth_method=searchbind"
            }),
            ("ldap_search_filter", {
                "label": ugettext_lazy("Search filter"),
                "help_text": ugettext_lazy(
                    "An optional filter string (e.g. '(objectClass=person)'). "
                    "In order to be valid, it must be enclosed in parentheses."
                ),
                "display": "ldap_auth_method=searchbind"
            }),
            ("ldap_user_dn_template", {
                "label": ugettext_lazy("User DN template"),
                "help_text": ugettext_lazy(
                    "The template used to construct a user's DN. It should "
                    "contain one placeholder (ie. %(user)s)"
                ),
                "display": "ldap_auth_method=directbind"
            }),
            ("ldap_password_attribute", {
                "label": ugettext_lazy("Password attribute"),
                "help_text": ugettext_lazy(
                    "The attribute used to store user passwords"),
            }),
            ("ldap_is_active_directory", {
                "label": ugettext_lazy("Active Directory"),
                "help_text": ugettext_lazy(
                    "Tell if the LDAP server is an Active Directory one")
            }),
            ("ldap_admin_groups", {
                "label": ugettext_lazy("Administrator groups"),
                "help_text": ugettext_lazy(
                    "Members of those LDAP Posix groups will be created as "
                    "domain administrators. Use ';' characters to separate "
                    "groups."
                )
            }),
            ("ldap_group_type", {
                "label": ugettext_lazy("Group type"),
                "help_text": ugettext_lazy(
                    "The LDAP group type to use with your directory."
                )
            }),
            ("ldap_groups_search_base", {
                "label": ugettext_lazy("Groups search base"),
                "help_text": ugettext_lazy(
                    "The distinguished name of the search base used to find "
                    "groups"
                )
            })
        ])
    }),
    ("dashboard", {
        "label": ugettext_lazy("Dashboard"),
        "params": collections.OrderedDict([
            ("rss_feed_url", {
                "label": ugettext_lazy("Custom RSS feed"),
                "help_text": ugettext_lazy(
                    "Display custom RSS feed to resellers and domain "
                    "administrators"
                )
            }),
            ("hide_features_widget", {
                "label": ugettext_lazy("Hide features widget"),
                "help_text": ugettext_lazy(
                    "Hide features widget for resellers and domain "
                    "administrators"
                )
            }),
        ])
    }),
    ("notifications", {
        "label": ugettext_lazy("Notifications"),
        "params": collections.OrderedDict([
            ("sender_address", {
                "label": ugettext_lazy("Sender address"),
                "help_text": ugettext_lazy(
                    "Email address used to send notifications.")
            })
        ])
    }),
    ("api", {
        "label": ugettext_lazy("Public API"),
        "params": collections.OrderedDict([
            ("enable_api_communication", {
                "label": ugettext_lazy("Enable communication"),
                "help_text": ugettext_lazy(
                    "Automatically checks if a newer version is available")
            }),
            ("check_new_versions", {
                "label": ugettext_lazy("Check new versions"),
                "display": "enable_api_communication=true",
                "help_text": ugettext_lazy(
                    "Automatically checks if a newer version is available")
            }),
            ("send_statistics", {
                "label": ugettext_lazy("Send statistics"),
                "display": "enable_api_communication=true",
                "help_text": ugettext_lazy(
                    "Send statistics to Modoboa public API "
                    "(counters and used extensions)")
            })
        ])
    }),
    ("misc", {
        "label": ugettext_lazy("Miscellaneous"),
        "params": collections.OrderedDict([
            ("inactive_account_threshold", {
                "label": ugettext_lazy("Inactive account threshold"),
                "help_text": ugettext_lazy(
                    "An account with a last login date greater than this "
                    "threshold (in days) will be considered as inactive"
                )
            }),
            ("top_notifications_check_interval", {
                "label": ugettext_lazy("Top notifications check interval"),
                "help_text": ugettext_lazy(
                    "Interval between two top notification checks (in seconds)"
                ),
            }),
            ("log_maximum_age", {
                "label": ugettext_lazy("Maximum log record age"),
                "help_text": ugettext_lazy(
                    "The maximum age in days of a log record"),
            }),
            ("items_per_page", {
                "label": ugettext_lazy("Items per page"),
                "help_text": ugettext_lazy("Number of displayed items per page")
            }),
            ("default_top_redirection", {
                "label": ugettext_lazy("Default top redirection"),
                "help_text": ugettext_lazy(
                    "The default redirection used when no application is "
                    "specified"
                ),
            })
        ])
    })
])
