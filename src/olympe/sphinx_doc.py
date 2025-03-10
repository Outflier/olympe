# -*- coding: utf-8 -*-

# Olympe sphinx-doc extension configuration file

from sphinx.ext.autodoc import FunctionDocumenter, ModuleLevelDocumenter
from sphinx.ext.autodoc import ClassDocumenter
from sphinx.domains.python import PyModulelevel, PyClasslike
from sphinx.util.logging import getLogger
from docutils.parsers.rst import Directive, directives

try:
    from olympe.arsdkng.messages import ArsdkMessage, ArsdkMessageType
    from olympe.arsdkng.enums import ArsdkEnum, ArsdkBitfield

    olympe_available = True
except Exception:
    olympe_available = False


logger = getLogger(__name__)


class ArsdkMessageDocumenter(FunctionDocumenter):
    directivetype = "function"
    objtype = "arsdk_message"
    priority = 100

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, ArsdkMessage)

    def add_directive_header(self, sig):
        self.directivetype = (
            "arsdk_cmd_message"
            if self.object.message_type is ArsdkMessageType.CMD
            else "arsdk_event_message"
        )
        ModuleLevelDocumenter.add_directive_header(self, sig)

    def format_args(self):
        args = self.object.args_name[:]
        args_default = self.object.args_default.copy()
        if self.object.message_type is ArsdkMessageType.CMD:
            args += ["_timeout"]
            args += ["_no_expect"]
            args_default.update(_timeout=self.object.timeout)
            args_default.update(_no_expect=False)
        else:
            args += ["_policy"]
            args_default.update(_policy="'check_wait'")
        args += ["_float_tol"]
        args_default.update(_float_tol=self.object.float_tol)
        ret = "{}".format(
            ", ".join(
                map(
                    lambda arg: arg + "=" + str(args_default[arg])
                    if arg in args_default
                    else arg,
                    args,
                )
            )
        )
        ret = "({})".format(ret)
        return ret

    def format_signature(self):
        return self.format_args()


class ArsdkEnumDocumenter(ClassDocumenter):
    directivetype = "class"
    objtype = "arsdk_enum"
    priority = 100

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, (ArsdkEnum.__class__, ArsdkEnum))

    def add_directive_header(self, sig):
        self.directivetype = "arsdk_enum"
        ModuleLevelDocumenter.add_directive_header(self, sig)

    def format_signature(self):
        return ""

    def document_members(self, all_members=False):
        sourcename = self.get_sourcename()
        if isinstance(self.object, ArsdkEnum.__class__):
            for value in self.object:
                self.add_line(
                    "    :{}: {} ({})".format(
                        value._name_, value.__doc__, value._value_
                    ),
                    sourcename,
                )
        else:
            super(ArsdkEnumDocumenter, self).document_members(all_members)


class DummyOptionSpec(object):
    """An option_spec allows any options."""

    def __getitem__(self, key):
        # type: (Any) -> Any
        return lambda x: x


class ArsdkFeatureDirective(Directive):

    option_spec = DummyOptionSpec()
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def __init__(self, name, arguments, options, *args):
        self.directive_args = args
        super(ArsdkFeatureDirective, self).__init__(name, arguments, options, *args)

    def run(self):
        automodule = directives._directives["automodule"]
        options = dict.fromkeys(("inherited-members", "members", "undoc-members"))
        message_module = "olympe.messages." + self.arguments[0]
        enum_module = "olympe.enums." + self.arguments[0]
        result = automodule(
            "automodule", [message_module], options, *self.directive_args
        ).run()
        result += automodule(
            "automodule", [enum_module], options, *self.directive_args
        ).run()
        return result


class PyArsdkCmdMessageDirective(PyModulelevel):
    """
    Description of an arsdk command message directive
    """

    allow_nesting = True

    def needs_arglist(self):
        # type: () -> bool
        return True

    def get_signature_prefix(self, sig):
        # type: (unicode) -> unicode
        return "command message"

    def get_index_text(self, modname, name_cls):
        # type: (unicode, unicode) -> unicode
        return "command_message"


class PyArsdkEventMessageDirective(PyModulelevel):
    """
    Description of an arsdk command message directive
    """

    allow_nesting = True

    def needs_arglist(self):
        # type: () -> bool
        return True

    def get_signature_prefix(self, sig):
        # type: (unicode) -> unicode
        return "event message"

    def get_index_text(self, modname, name_cls):
        # type: (unicode, unicode) -> unicode
        return "event_message"


class PyArsdkEnumDirective(PyClasslike):
    """
    Description of an arsdk command message directive
    """

    allow_nesting = True

    def get_signature_prefix(self, sig):
        # type: (unicode) -> unicode
        return "enum"

    def get_index_text(self, modname, name_cls):
        # type: (unicode, unicode) -> unicode
        return "enum"


def arsdk_skip_member(app, what, name, obj, skip, options):
    if isinstance(obj, ArsdkBitfield.__class__):
        return True
    return False


def setup(app):
    if not olympe_available:
        logger.warning("Olympe ARSDK message documentation will not be available")
    app.add_autodocumenter(ArsdkMessageDocumenter)
    app.add_autodocumenter(ArsdkEnumDocumenter)
    app.add_directive("auto_arsdkfeature", ArsdkFeatureDirective)
    app.add_directive_to_domain("py", "arsdk_cmd_message", PyArsdkCmdMessageDirective)
    app.add_directive_to_domain(
        "py", "arsdk_event_message", PyArsdkEventMessageDirective
    )
    app.add_directive_to_domain("py", "arsdk_enum", PyArsdkEnumDirective)
    app.connect("autodoc-skip-member", arsdk_skip_member)
