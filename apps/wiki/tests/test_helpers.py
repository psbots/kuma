from nose.tools import eq_

from django.contrib.auth.models import User

from wiki.tests import TestCaseBase, revision, normalize_html
from wiki.helpers import (revisions_unified_diff,
                          section_extract, section_hide,
                          zone_section_extract,
                          document_zone_management_links)
from wiki.models import DocumentZone


class ContentHelperTests(TestCaseBase):

    def test_section_extract(self):
        src = """
            <h2>Foo</h2>
            <p>Bar</p>
            <h3 id="Quick_Links">Quick Links</h3>
            <p>Foo, yay</p>
            <h2>Baz</h2>
            <p>Baz</p>
        """
        expected = """
            <p>Foo, yay</p>
        """
        result = section_extract(src, 'Quick_Links')
        eq_(normalize_html(expected), normalize_html(result))

    def test_section_hide(self):
        src = """
            <h2>Foo</h2>
            <p>Bar</p>
            <h3 id="Quick_Links">Quick Links</h3>
            <p>Foo, yay</p>
            <h2>Baz</h2>
            <p>Baz</p>
        """
        expected = """
            <h2>Foo</h2>
            <p>Bar</p>
            <!-- -->
            <h2>Baz</h2>
            <p>Baz</p>
        """
        result = section_hide(src, 'Quick_Links')
        eq_(normalize_html(expected), normalize_html(result))


class RevisionsUnifiedDiffTests(TestCaseBase):
    fixtures = ['test_users.json']

    def test_from_revision_none(self):
        rev = revision()
        try:
            diff = revisions_unified_diff(None, rev)
        except AttributeError:
            self.fail("Should not throw AttributeError")
        eq_("Diff is unavailable.", diff)


class DocumentZoneTests(TestCaseBase):
    """Tests for DocumentZone helpers"""
    fixtures = ['test_users.json']

    def setUp(self):
        super(DocumentZoneTests, self).setUp()

        self.root_links_content = """
            <p>Links content</p>
        """
        self.root_content = """
            <h4 id="links">Links</h4>
            %s
        """ % (self.root_links_content)

        root_rev = revision(title='ZoneRoot', slug='ZoneRoot',
                            content=self.root_content,
                            is_approved=True, save=True)
        self.root_doc = root_rev.document
        self.root_doc.rendered_html = self.root_content
        self.root_doc.save()

        self.root_zone = DocumentZone(document=self.root_doc)
        self.root_zone.save()

        sub_rev = revision(title='SubPage', slug='SubPage',
                           content='This is a subpage',
                           is_approved=True, save=True)
        self.sub_doc = sub_rev.document
        self.sub_doc.parent_topic = self.root_doc
        self.sub_doc.rendered_html = sub_rev.content
        self.sub_doc.save()

        self.sub_sub_links_content = """
            <p>Sub-page links content</p>
        """
        self.sub_sub_content = """
            <h4 id="links">Links</h4>
            %s
        """ % (self.sub_sub_links_content)

        sub_sub_rev = revision(title='SubSubPage', slug='SubSubPage',
                           content='This is a subpage',
                           is_approved=True, save=True)
        self.sub_sub_doc = sub_sub_rev.document
        self.sub_sub_doc.parent_topic = self.sub_doc
        self.sub_sub_doc.rendered_html = self.sub_sub_content
        self.sub_sub_doc.save()

        other_rev = revision(title='otherPage', slug='otherPage',
                            content='This is an other page',
                            is_approved=True, save=True)
        self.other_doc = other_rev.document
        self.other_doc.save()

    def test_zone_section_extract(self):
        root_result = zone_section_extract(self.root_doc, 'links')
        eq_(normalize_html(root_result),
            normalize_html(self.root_links_content))

        sub_result = zone_section_extract(self.sub_doc, 'links')
        eq_(normalize_html(sub_result),
            normalize_html(self.root_links_content))

        sub_sub_result = zone_section_extract(self.sub_sub_doc, 'links')
        eq_(normalize_html(sub_sub_result),
            normalize_html(self.sub_sub_links_content))

    def test_document_zone_links(self):
        admin = User.objects.filter(is_superuser=True)[0]
        random = User.objects.filter(is_superuser=False)[0]
        cases = [
            (admin, self.root_doc, False, True),
            (random, self.root_doc, False, False),
            (admin, self.sub_doc, True, True),
            (random, self.sub_doc, False, False),
            (admin, self.other_doc, True, False),
            (random, self.other_doc, False, False),
        ]
        for (user, doc, add, change) in cases:
            result_links = document_zone_management_links(user, doc)
            eq_(add, (result_links['add'] is not None))
            eq_(change, (result_links['change'] is not None))
