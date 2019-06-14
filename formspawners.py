from wrapspawner import WrapSpawner
from traitlets import Unicode, Type

import os

from traitlets.config.configurable import HasTraits

__all__ = ['ParamForm', 'FormMixin', 'WrapFormSpawner']


class ParamForm(HasTraits):
    """ Read a form to render from a file (set via source attribute) and
        include code to shape the form data into what the spawner needs. Reads
        the file path relative to the directory *this* module is installed in

        This class will be the @form_cls type attached to a custom spawner

        Subclass as needed to include your own methods
    """

    source = Unicode('')

    def __init__(self, spawner):
        self.spawner = spawner

    def generate(self):
        path = os.path.join(os.path.dirname(__file__), self.source)
        with open(path) as f:
            return f.read()

    def massage_options(self, formdata):
        return {k: v[0] for k, v in formdata.items()}


class FormMixin(HasTraits):
    """ Class to mix into a custom spawner that injects the form_cls attribute.

        Mix it in as the *first* parent so as to override the native options form stuff

        Calls the referenced form_cls (instantiated) methods to return formdata
        to the spawner.
    """

    form_cls = Type(ParamForm, help="Type of form class to use").tag(config=True)

    @staticmethod
    def options_form(self):
        return self.form_cls(self).generate()

    def options_from_form(self, formdata):
        return self.form_cls(self).massage_options(formdata)


class WrapFormSpawner(FormMixin, WrapSpawner):
    """ WrapSpawner modification to select the child class based on the
        form information generated by a form-class above. Subclasses must
        implement a set_class method that gets the formdata and must use that
        to return a Spawner class to use
    """

    def options_from_form(self, formdata):
        self.child_class = self.set_class(formdata)
        self.child_class.formdata = formdata
        if hasattr(self.child_class, 'form_cls'):
            self.log.debug("WrapForm: Set child config from child class's form_cls: %s",
                           self.child_class.form_cls)
            self.child_config = self.child_class.form_cls(self).massage_options(formdata)
            self.child_class.user_options = self.child_config
        else:
            self.log.debug("No child config found")
            self.child_config = {}
        self.log.info("Spawner child-config: %s", self.child_config)
        return {}

    def set_class(self, data):
        raise NotImplementedError('Must implement in subclass')
