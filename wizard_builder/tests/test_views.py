import json
from unittest import skip

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.test import TestCase

from ..forms import PageForm
from ..models import Checkbox, Choice, Page, RadioButton, SingleLineText
from ..views import ConfigurableFormWizard
from .test_app.models import Report

User = get_user_model()


def sort_json(text):
    return sorted(json.loads(text), key=lambda x: x['id'])


def get_body(response):
    return response.content.decode('utf-8')


class FormBaseTest(TestCase):

    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()
        self.page1 = Page.objects.create()
        self.page1.sites.add(self.site.id)
        self.page2 = Page.objects.create()
        self.page2.sites.add(self.site.id)
        self.question1 = SingleLineText.objects.create(
            text="first question", page=self.page1)
        self.question2 = SingleLineText.objects.create(
            text="2nd question", page=self.page2)

    def _get_wizard_response(self, wizard, form_list, **kwargs):
        # simulate what wizard does on final form submit
        wizard.processed_answers = wizard.process_answers(
            form_list=form_list, form_dict=dict(enumerate(form_list)))
        return get_body(
            wizard.done(
                form_list=form_list,
                form_dict=dict(
                    enumerate(form_list)),
                **kwargs))


class WizardIntegratedTest(FormBaseTest):

    def setUp(self):
        super(WizardIntegratedTest, self).setUp()
        User.objects.create_user(username='dummy', password='dummy')
        self.client.login(username='dummy', password='dummy')
        self.request = HttpRequest()
        self.request.GET = {}
        self.request.method = 'GET'
        self.request.user = User.objects.get(username='dummy')

    form_url = '/wizard/new/0/'
    report_key = 'solidasarock1234rock'

    def _answer_page_one(self):
        return self.client.post(
            self.form_url,
            data={'0-question_%i' % self.question1.pk: 'test answer',
                  'wizard_goto_step': 1,
                  'form_wizard-current_step': 0},
            follow=True)

    def _answer_page_two(self, response):
        return self.client.post(
            response.redirect_chain[0][0],
            data={
                '1-question_%i' %
                self.question2.pk: 'another answer to a different question',
                'wizard_goto_step': 2,
                'form_wizard-current_step': 1},
            follow=True)

    def test_wizard_generates_correct_number_of_pages(self):
        page3 = Page.objects.create()
        page3.sites.add(self.site.id)
        SingleLineText.objects.create(text="first page question", page=page3)
        SingleLineText.objects.create(
            text="one more first page question",
            page=page3,
            position=2)
        SingleLineText.objects.create(
            text="another first page question", page=page3, position=1)
        wizard = ConfigurableFormWizard.wizard_factory(site_id=self.site.id)()
        self.assertEqual(len(wizard.form_list), 3)

    def test_displays_first_page(self):
        response = self.client.get(self.form_url)
        self.assertIsInstance(response.context['form'], PageForm)
        self.assertContains(
            response,
            'name="0-question_%i"' %
            self.question1.pk)
        self.assertNotContains(
            response,
            'name="0-question_%i"' %
            self.question2.pk)

    def test_form_advances_to_second_page(self):
        response = self.client.post(
            self.form_url,
            data={'0-question_%i"' % self.question1.pk: 'A new report',
                  'wizard_goto_step': 1,
                  'form_wizard-current_step': 0},
            follow=True)

        self.assertTrue(
            response.redirect_chain[0][0].endswith("/wizard/new/1/"))
        self.assertContains(
            response,
            'name="1-question_%i"' %
            self.question2.pk)
        self.assertNotContains(
            response,
            'name="1-question_%i"' %
            self.question1.pk)

    def test_can_alter_form_without_restarting_server(self):
        new_question = SingleLineText.objects.create(
            text="another first page question", page=self.page1)
        response = self.client.get(self.form_url)
        self.assertContains(response, 'name="0-question_%i"' % new_question.pk)

    @skip('TODO: evaluate if this is a valid test')
    def test_done_serializes_questions(self):
        self.maxDiff = None

        radio_button_q = RadioButton.objects.create(
            text="this is a radio button question", page=self.page2)
        for i in range(5):
            Choice.objects.create(
                text="This is choice %i" %
                i, question=radio_button_q)

        response = self._answer_page_one()
        response = self.client.post(
            response.redirect_chain[0][0],
            data={
                '1-question_%i' %
                self.question2.pk: 'another answer to a different question',
                '1-question_%i' %
                radio_button_q.pk: radio_button_q.choice_set.all()[2].pk,
                'wizard_goto_step': 2,
                'form_wizard-current_step': 1},
            follow=True)

        object_ids = [choice.pk for choice in radio_button_q.choice_set.all()]
        selected_id = object_ids[2]
        object_ids.insert(0, radio_button_q.pk)
        object_ids.insert(0, selected_id)
        object_ids.insert(0, self.question2.pk)
        object_ids.insert(0, self.question1.pk)

        json_report = """[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "another answer to a different question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    },
    { "answer": "%i",
      "id": %i,
      "section": 1,
      "question_text": "this is a radio button question",
            "choices": [{"id": %i, "choice_text": "This is choice 0"},
                  {"id": %i, "choice_text": "This is choice 1"},
                  {"id": %i, "choice_text": "This is choice 2"},
                  {"id": %i, "choice_text": "This is choice 3"},
                  {"id": %i, "choice_text": "This is choice 4"}],
      "type": "RadioButton"
    }
  ]""" % tuple(object_ids)

        self.assertEqual(sort_json(get_body(response)), sort_json(json_report))

    @skip('TODO: evaluate if this is a valid test')
    def test_form_saves_checkboxes(self):
        checkbox_q = Checkbox.objects.create(
            text="this is a checkbox question", page=self.page2)
        for i in range(5):
            Choice.objects.create(
                text="This is checkbox choice %i" %
                i, question=checkbox_q)
        selected_1 = checkbox_q.choice_set.all()[0].pk
        selected_2 = checkbox_q.choice_set.all()[4].pk

        response = self._answer_page_one()
        response = self.client.post(
            response.redirect_chain[0][0],
            data={
                '1-question_%i' %
                self.question2.pk: 'another answer to a different question',
                '1-question_%i' %
                checkbox_q.pk: [
                    str(selected_1),
                    str(selected_2)],
                'wizard_goto_step': 2,
                'form_wizard-current_step': 1},
            follow=True)
        output = get_body(response)
        self.assertIn("checkbox choice", output)
        self.assertIn('["%i", "%i"]' % (selected_1, selected_2), output)

    @skip('TODO: evaluate if this is a valid test')
    def test_pages_with_multiple(self):
        multiple_page = Page.objects.create(
            multiple=True,
            name_for_multiple="form",
        )
        multiple_page.sites.add(self.site.id)
        q1 = SingleLineText.objects.create(
            text="question 1", page=multiple_page)
        q2 = SingleLineText.objects.create(
            text="question 2", page=multiple_page)

        response = self._answer_page_one()
        response = self._answer_page_two(response)
        response = self.client.post(
            response.redirect_chain[0][0],
            data={"2-TOTAL_FORMS": 2,
                  "2-INITIAL_FORMS": 0,
                  '2-0-question_%i' % q1.pk: "question 1 first answer",
                  '2-0-question_%i' % q2.pk: "question 2 first answer",
                  '2-1-question_%i' % q1.pk: "question 1 second answer",
                  '2-1-question_%i' % q2.pk: "question 2 second answer",
                  'wizard_goto_step': 3,
                  'form_wizard-current_step': 2},
            follow=True)

        output = json.loads(get_body(response))
        self.assertEqual(multiple_page.pk, output[2]['page_id'])
        answers = [sort_json(json.dumps(answer))
                   for answer in output[2]['answers']]
        self.assertEquals("question 1 first answer", answers[0][0]['answer'])
        self.assertEquals("question 2 first answer", answers[0][1]['answer'])
        self.assertEquals("question 1 second answer", answers[1][0]['answer'])
        self.assertEquals("question 2 second answer", answers[1][1]['answer'])

    def test_can_skip_to_end(self):
        response = self.client.post(
            self.form_url,
            data={'0-question_%i' % self.question1.pk: 'test answer',
                  'wizard_goto_step': 'end',
                  'form_wizard-current_step': 0},
            follow=True)
        output = get_body(response)
        self.assertIn('"answer": "test answer"', output)


class EditRecordFormTest(FormBaseTest):
    form_url = '/wizard/edit/%s/0/'

    def setUp(self):
        super(EditRecordFormTest, self).setUp()
        self.report_text = """[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "another answer to a different question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    }
  ]""" % (self.question1.pk, self.question2.pk)
        self.report = Report.objects.create(text=self.report_text)

    def test_edit_record_page_renders_first_page(self):
        response = self.client.get(self.form_url % self.report.pk, follow=True)
        self.assertTemplateUsed(response, 'wizard_builder/wizard_form.html')
        self.assertIsInstance(response.context['form'], PageForm)
        self.assertContains(
            response,
            'name="0-question_%i"' %
            self.question1.pk)
        self.assertNotContains(
            response,
            'name="0-question_%i"' %
            self.question2.pk)

    def test_edit_form_advances_to_second_page(self):
        response = self.client.post(
            (self.form_url % self.report.pk),
            data={'0-question_1': "first answer",
                  'wizard_goto_step': 1,
                  'form_wizard' + str(self.report.id) + '-current_step': 0},
            follow=True
        )
        self.assertTemplateUsed(response, 'wizard_builder/wizard_form.html')
        self.assertIsInstance(response.context['form'], PageForm)
        self.assertContains(
            response,
            'name="1-question_%i"' %
            self.question2.pk)
        self.assertNotContains(
            response,
            'name="1-question_%i"' %
            self.question1.pk)

    def test_initial_is_passed_to_forms(self):
        response = self.client.get(self.form_url % self.report.pk, follow=True)
        form = response.context['form']
        self.assertIn('test answer', form.initial.values())
        self.assertIn(
            'another answer to a different question',
            form.initial.values())
        self.assertIn('test answer', get_body(response))
        self.assertNotIn(
            'another answer to a different question',
            get_body(response))
        response = self.client.post(
            self.form_url % self.report.pk,
            data={'0-question_1': "first answer",
                  'wizard_goto_step': 1,
                  'form_wizard' + str(self.report.id) + '-current_step': 0},
            follow=True
        )
        self.assertNotIn('test answer', get_body(response))
        self.assertIn(
            'another answer to a different question',
            get_body(response))

    @skip('TODO: evaluate if this is a valid test')
    def test_edit_modifies_record(self):
        response = self.client.post(
            (self.form_url % self.report.pk),
            data={'0-question_1': "first answer edited",
                  'wizard_goto_step': 1,
                  'form_wizard' + str(self.report.id) + '-current_step': 0},
            follow=True
        )

        response = self.client.post(
            response.redirect_chain[0][0],
            data={'1-question_%i' % self.question2.pk: '2nd edited answer',
                  'wizard_goto_step': 2,
                  'form_wizard' + str(self.report.id) + '-current_step': 1},
            follow=True)

        edited_form = json.loads(get_body(response))
        self.assertEqual(edited_form[0]['answer'], 'first answer edited')
        self.assertEqual(edited_form[1]['answer'], '2nd edited answer')
