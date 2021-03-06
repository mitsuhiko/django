from __future__ import with_statement
import os
from django.conf import settings, global_settings
from django.test import TestCase, signals
from django.test.utils import override_settings


# @override_settings(TEST='override')
class FullyDecoratedTestCase(TestCase):

    def test_override(self):
        self.assertEqual(settings.TEST, 'override')

    @override_settings(TEST='override2')
    def test_method_override(self):
        self.assertEqual(settings.TEST, 'override2')

FullyDecoratedTestCase = override_settings(TEST='override')(FullyDecoratedTestCase)

class SettingGetter(object):
    def __init__(self):
        self.test = getattr(settings, 'TEST', 'undefined')

testvalue = None

def signal_callback(sender, setting, value, **kwargs):
    global testvalue
    testvalue = value

signals.setting_changed.connect(signal_callback, sender='TEST')

class SettingsTests(TestCase):

    def test_override(self):
        settings.TEST = 'test'
        self.assertEqual('test', settings.TEST)
        with self.settings(TEST='override'):
            self.assertEqual('override', settings.TEST)
        self.assertEqual('test', settings.TEST)
        del settings.TEST

    def test_override_change(self):
        settings.TEST = 'test'
        self.assertEqual('test', settings.TEST)
        with self.settings(TEST='override'):
            self.assertEqual('override', settings.TEST)
            settings.TEST = 'test2'
        self.assertEqual('test', settings.TEST)
        del settings.TEST

    def test_override_doesnt_leak(self):
        self.assertRaises(AttributeError, getattr, settings, 'TEST')
        with self.settings(TEST='override'):
            self.assertEqual('override', settings.TEST)
            settings.TEST = 'test'
        self.assertRaises(AttributeError, getattr, settings, 'TEST')

    @override_settings(TEST='override')
    def test_decorator(self):
        self.assertEqual('override', settings.TEST)

    def test_context_manager(self):
        self.assertRaises(AttributeError, getattr, settings, 'TEST')
        override = override_settings(TEST='override')
        self.assertRaises(AttributeError, getattr, settings, 'TEST')
        override.enable()
        self.assertEqual('override', settings.TEST)
        override.disable()
        self.assertRaises(AttributeError, getattr, settings, 'TEST')

    def test_class_decorator(self):
        self.assertEqual(SettingGetter().test, 'undefined')
        DecoratedSettingGetter = override_settings(TEST='override')(SettingGetter)
        self.assertEqual(DecoratedSettingGetter().test, 'override')
        self.assertRaises(AttributeError, getattr, settings, 'TEST')

    def test_signal_callback_context_manager(self):
        self.assertRaises(AttributeError, getattr, settings, 'TEST')
        with self.settings(TEST='override'):
            self.assertEqual(testvalue, 'override')

    @override_settings(TEST='override')
    def test_signal_callback_decorator(self):
        self.assertEqual(testvalue, 'override')

    #
    # Regression tests for #10130: deleting settings.
    #

    def test_settings_delete(self):
        settings.TEST = 'test'
        self.assertEqual('test', settings.TEST)
        del settings.TEST
        self.assertRaises(AttributeError, getattr, settings, 'TEST')

    def test_settings_delete_wrapped(self):
        self.assertRaises(TypeError, delattr, settings, '_wrapped')



class TrailingSlashURLTests(TestCase):
    settings_module = settings

    def setUp(self):
        self._original_media_url = self.settings_module.MEDIA_URL

    def tearDown(self):
        self.settings_module.MEDIA_URL = self._original_media_url

    def test_blank(self):
        """
        If blank, no DeprecationWarning error will be raised, even though it
        doesn't end in a slash.
        """
        self.settings_module.MEDIA_URL = ''
        self.assertEqual('', self.settings_module.MEDIA_URL)

    def test_end_slash(self):
        """
        MEDIA_URL works if you end in a slash.
        """
        self.settings_module.MEDIA_URL = '/foo/'
        self.assertEqual('/foo/', self.settings_module.MEDIA_URL)

        self.settings_module.MEDIA_URL = 'http://media.foo.com/'
        self.assertEqual('http://media.foo.com/',
                         self.settings_module.MEDIA_URL)

    def test_no_end_slash(self):
        """
        MEDIA_URL raises an DeprecationWarning error if it doesn't end in a
        slash.
        """
        import warnings
        warnings.filterwarnings('error', 'If set, MEDIA_URL must end with a slash', DeprecationWarning)

        def setattr_settings(settings_module, attr, value):
            setattr(settings_module, attr, value)

        self.assertRaises(DeprecationWarning, setattr_settings,
                          self.settings_module, 'MEDIA_URL', '/foo')

        self.assertRaises(DeprecationWarning, setattr_settings,
                          self.settings_module, 'MEDIA_URL',
                          'http://media.foo.com')

    def test_double_slash(self):
        """
        If a MEDIA_URL ends in more than one slash, presume they know what
        they're doing.
        """
        self.settings_module.MEDIA_URL = '/stupid//'
        self.assertEqual('/stupid//', self.settings_module.MEDIA_URL)

        self.settings_module.MEDIA_URL = 'http://media.foo.com/stupid//'
        self.assertEqual('http://media.foo.com/stupid//',
                         self.settings_module.MEDIA_URL)


class EnvironmentVariableTest(TestCase):
    """
    Ensures proper settings file is used in setup_environ if
    DJANGO_SETTINGS_MODULE is set in the environment.
    """
    def setUp(self):
        self.original_value = os.environ.get('DJANGO_SETTINGS_MODULE')

    def tearDown(self):
        if self.original_value:
            os.environ['DJANGO_SETTINGS_MODULE'] = self.original_value
        elif 'DJANGO_SETTINGS_MODULE' in os.environ:
            del(os.environ['DJANGO_SETTINGS_MODULE'])

    def test_env_var_used(self):
        """
        If the environment variable is set, do not ignore it. However, the
        kwarg original_settings_path takes precedence.

        This tests both plus the default (neither set).
        """
        from django.core.management import setup_environ

        # whatever was already there
        original_module =  os.environ.get(
            'DJANGO_SETTINGS_MODULE',
            'the default'
        )

        # environment variable set by user
        user_override = 'custom.settings'

        # optional argument to setup_environ
        orig_path = 'original.path'

        # expect default
        setup_environ(global_settings)
        self.assertEquals(
            os.environ.get('DJANGO_SETTINGS_MODULE'),
            original_module
        )

        # override with environment variable
        os.environ['DJANGO_SETTINGS_MODULE'] = user_override
        setup_environ(global_settings)

        self.assertEquals(
            os.environ.get('DJANGO_SETTINGS_MODULE'),
            user_override
        )

        # pass in original_settings_path (should take precedence)
        os.environ['DJANGO_SETTINGS_MODULE'] = user_override
        setup_environ(global_settings, original_settings_path = orig_path)

        self.assertEquals(
            os.environ.get('DJANGO_SETTINGS_MODULE'),
            orig_path
        )
