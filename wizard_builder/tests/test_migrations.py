from django_migration_testcase import MigrationTest


class QuestionPageMigrationTest(MigrationTest):

    app_name = 'wizard_builder'
    before = '0008_remove_textpage'
    after = '0011_rename_questionpage_attrs'

    def test_attributes_populated(self):
        OldQuestionPage = self.get_model_before('wizard_builder.QuestionPage')
        old_page = OldQuestionPage.objects.create(
            position=20,
            section=1,
        )
        old_page.sites.add(1)
        old_page_sites_count = old_page.sites.count()

        self.run_migration()
        NewQuestionPage = self.get_model_after('wizard_builder.QuestionPage')
        new_page = NewQuestionPage.objects.first()

        self.assertEqual(old_page.section, new_page.section)
        self.assertEqual(old_page.position, new_page.position)
        self.assertEqual(old_page_sites_count, new_page.sites.count())


class PageIDMigrationTest(MigrationTest):

    app_name = 'wizard_builder'
    before = '0011_rename_questionpage_attrs'
    after = '0013_create_page_id'

    def test_attributes_populated(self):
        OldQuestionPage = self.get_model_before('wizard_builder.QuestionPage')
        old_page = OldQuestionPage.objects.create()

        self.run_migration()
        NewPage = self.get_model_after('wizard_builder.Page')
        new_page = NewPage.objects.first()

        self.assertEqual(old_page.pk, new_page.pk)
