"""Tests for arXiv taxonomy module."""
from unittest import TestCase
from datetime import date
from .definitions import GROUPS, ARCHIVES, \
    ARCHIVES_ACTIVE, CATEGORIES, ARCHIVES_SUBSUMED, \
    LEGACY_ARCHIVE_AS_PRIMARY, LEGACY_ARCHIVE_AS_SECONDARY, CATEGORY_ALIASES
from .category import Category, Archive, Group, BaseTaxonomy


class TestTaxonomy(TestCase):
    """Tests for the arXiv category taxonomy definitions."""

    def test_groups(self):
        """Tests for the highest level of the category taxonomy (groups)."""
        for key, value in GROUPS.items():
            self.assertRegexpMatches(key, r'^grp_[a-z\-_]+$')
            self.assertIsInstance(value.id, str, 'id is a str')
            self.assertIsInstance(value.start_year, int, 'start_year is an integer')
            self.assertGreater(value.start_year, 1990, 'start_year > 1990')
            if value.default_archive:
                self.assertIn(
                    value.default_archive,
                    ARCHIVES,
                    'default_archive {} is a valid archive'.format(
                        value.default_archive)
                )
            self.assertIsInstance(value.full_name, str)
            self.assertIsInstance(value.canonical, str)
            self.assertIn(value.canonical,GROUPS.keys(), "all groups currently cannonical for themselves")
            self.assertIsInstance(value.display(), str)
            archives=value.get_archives()
            self.assertGreater(len(archives),0,"group contains archives")
            self.assertTrue(all(isinstance(item, Archive) for item in archives), "archives fetched are Archive")        

    def test_archives(self):
        """Tests for the middle level of the category taxonomy (archives)."""
        for key, value in ARCHIVES.items():
            self.assertIsInstance(value.id, str, 'id is a str')
            self.assertIsInstance(value.full_name, str, 'full_name is a str')
            self.assertIsInstance(value.start_date, date)
            self.assertGreaterEqual(value.start_date, date(1991, 8, 1))
            if value.end_date:
                self.assertIsInstance(value.end_date, date)
                self.assertGreater(
                    value.end_date,
                    value.start_date,
                    'end_date greater than start_date'
                )
            self.assertIsInstance(value.display(), str)
            self.assertIsInstance(value.canonical, str)
            self.assertIn(value.canonical, list(CATEGORIES.keys()).append(value.id), "cannonical name either the archive or a category")

            self.assertTrue(all(isinstance(item, Category) for item in value.get_categories()), "categories fetched are Category")
            self.assertIsInstance(value.in_group, str, 'in_group is a str')
            self.assertIn(value.in_group, GROUPS.keys(), f'{value.in_group} is a valid group')
            self.assertIsInstance(value.get_group(), Group, "fetches group object")
            self.assertEqual(value.in_group, value.get_group().id, "in_group and get_group point to same group")
            if value.alt_name:
                self.assertIn(key, ARCHIVES_SUBSUMED.keys(), "alternate names are recorded")

    def test_active_archives(self):
        """Tests for active (non-defunct) archives."""
        for key, value in ARCHIVES_ACTIVE.items():
            self.assertFalse(value.end_date)

    def test_archives_subsumed(self):
        """Tests for defunct archives that have been subsumed by categories."""
        for key, value in ARCHIVES_SUBSUMED.items():
            self.assertIn(key, ARCHIVES.keys(), '{} is a valid archive'.format(key))
            subsumed=ARCHIVES[key]
            self.assertIsInstance(subsumed.end_date,date,"is a defunct archive")
            self.assertIn(
                value,
                CATEGORIES.keys(),
                '{} is a valid category'.format(value)
            )
            subsuming_cat=CATEGORIES[value]
            self.assertFalse(subsuming_cat.get_archive().end_date, '{} is not in a defunct archive'.format(value))
            self.assertEqual(subsumed.canonical, value, "canonical of archive is subsuming category")
            self.assertEqual(subsumed.alt_name, value, "subsumed archive knows its pair")
            self.assertEqual(subsuming_cat.alt_name, key, "subsuming category knows its old archive")
            self.assertEqual(subsuming_cat.display(True), subsuming_cat.display(False), "display string always the same for canonical name")
            self.assertNotEqual(subsumed.display(True), subsumed.display(False), "display has different text for canonincal and non canonical options")

    def test_legacy_archives_as_categories(self):
        """Test for archives that were used as primary/secondary categories."""
        for key, value in LEGACY_ARCHIVE_AS_PRIMARY.items():
            self.assertIn(key, ARCHIVES.keys(), '{} is a valid archive'.format(key))
            self.assertIsInstance(value, date)

        for key, value in LEGACY_ARCHIVE_AS_SECONDARY.items():
            self.assertIn(key, ARCHIVES.keys(), '{} is a valid archive'.format(key))
            self.assertIsInstance(value, date)

    def test_categories(self):
        """Test for the lowest level of the category taxonomy (categories)."""
        for key, value in CATEGORIES.items():
            self.assertIsInstance(value.id, str, 'id is a str')
            self.assertIsInstance(value.full_name, str, 'full_name is a str')
            self.assertIsInstance(value.is_active, bool, 'is active is bool')

            self.assertIsInstance(value.in_archive, str, 'in_archive is a str')
            self.assertIn(value.in_archive, ARCHIVES.keys(), f'{value.in_archive} is a valid archive')
            parent=value.get_archive()
            self.assertIsInstance(parent, Archive, "fetches Archive object")
            self.assertEqual(value.in_archive, parent.id, "in_archive and get_archive point to same archive")
            self.assertTrue(parent.is_active,"category in active archive")

            self.assertIsInstance(value.canonical, str, "cannonical id is string")
            self.assertIn(value.canonical, CATEGORIES.keys(), "cannonical name is a category")
            self.assertIsInstance(value.display(), str, "display test is string")

            if value.alt_name:
                self.assertIn(key, list(ARCHIVES_SUBSUMED.values())+list(CATEGORY_ALIASES.values())+list(CATEGORY_ALIASES.keys()), "alternate names are recorded")

    def test_aliases(self):
        """Test for category aliases. (value is the canonical name)"""
        for key, value in CATEGORY_ALIASES.items():
            self.assertNotEqual(key, value,
                                'alias should be different from canonical')
            self.assertIn(key, CATEGORIES.keys())
            self.assertIn(value, CATEGORIES.keys())
            canon=CATEGORIES[value]
            not_canon=CATEGORIES[key]
            self.assertIn(f'{key} is an alias for {value}.',
                          not_canon.description,
                          'Category description for an alias should indicate '
                          'that it is an alias for some other category')
            
            self.assertEqual(canon.id, canon.canonical, "canonical category is canonical")
            self.assertNotEqual(not_canon.id, not_canon.canonical, "non-canonical category is not canonical")
            self.assertEqual(canon.id, not_canon.canonical, "alias knows its canonical category")
            self.assertEqual(not_canon.alt_name, canon.id, "alias knows its pair")
            self.assertEqual(canon.alt_name, not_canon.id, "alias knows its pair")
            self.assertEqual(canon.display(True), canon.display(False), "display string always the same for canonical name")
            self.assertNotEqual(not_canon.display(True), not_canon.display(False), "display has different text for canonincal and non canonical options")

