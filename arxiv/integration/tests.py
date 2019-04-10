"""Tests for :mod:`.integration`."""

from unittest import TestCase
from .meta import MetaIntegration


class ContextSingleton:
    """Mimics context switching in Flask."""

    def __init__(self):
        """Make a place to put contextualized instances."""
        self.current_context = -1
        self.contexts = {}

    def set_context(self, context):
        """Change to a different context."""
        self.current_context = context

    def get_context(self):
        """Get the current context."""
        return self.current_context


class TestMetaIntegration(TestCase):
    """Tests for :class:`.MetaIntegration`."""

    @classmethod
    def setUpClass(cls):
        """Define a simple web service integration class."""
        cls.ctx = ContextSingleton()

        class TestIntegration(metaclass=MetaIntegration):
            """Test service integration class."""

            def __init__(self, context):
                self.context = context

            @classmethod
            def current_session(ccls):
                """Get or create an instance for the current context."""
                current_context = cls.ctx.get_context()
                if current_context not in cls.ctx.contexts:
                    cls.ctx.contexts[current_context] = ccls(current_context)
                return cls.ctx.contexts[current_context]

            def get_something(self):
                """Do something based on the instance state."""
                return self.context + self.context

            def get_instance(self):
                """Get the instance that owns this bound method."""
                return self

        cls.TestIntegration = TestIntegration

    def setUp(self):
        """Clear all contexts."""
        self.ctx.contexts.clear()

    def test_get_instance(self):
        """Can work with instances of the class directly."""
        instance = self.TestIntegration('bar')
        self.assertIsInstance(instance, self.TestIntegration)
        self.assertEqual(instance.context, 'bar')
        self.assertEqual(instance.get_something(), 'barbar')

    def test_get_contextualized_instance(self):
        """Can get a contextualized instance."""
        self.ctx.set_context(2)
        instance = self.TestIntegration.current_session()
        self.assertIsInstance(instance, self.TestIntegration)
        self.assertEqual(instance.context, 2)
        self.assertEqual(instance.get_something(), 4)

        self.ctx.set_context(3)
        second_instance = self.TestIntegration.current_session()
        self.assertIsInstance(second_instance, self.TestIntegration)
        self.assertEqual(second_instance.context, 3)
        self.assertEqual(second_instance.get_something(), 6)

        self.assertNotEqual(id(second_instance), id(instance))

    def test_get_contextualized_method(self):
        """Get the method of the context-bound instance."""
        self.ctx.set_context(1)
        first_method = self.TestIntegration.get_instance

        self.ctx.set_context(2)
        second_method = self.TestIntegration.get_instance

        self.ctx.set_context(1)
        third_method = self.TestIntegration.get_instance

        self.assertNotEqual(id(first_method()), id(second_method()),
                            "These methods belong to different instances"
                            " because they were obtained in different"
                            " contexts.")
        self.assertEqual(id(first_method()), id(third_method()),
                         "These methods belong to the same instance because"
                         " they were obtained in the same context.")
