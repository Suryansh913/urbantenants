import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import RoommateConnectionRequest, RoommateProfile
from .utils import calculate_match_percentage

User = get_user_model()


def make_profile(user, **overrides):
    defaults = dict(
        full_name="Test User",
        age=21,
        gender="male",
        college="Test College",
        preferred_location="Gharuan",
        budget_min=3000,
        budget_max=4000,
        accommodation_type="pg",
        sharing_type="double",
        move_in_date=datetime.date.today() + datetime.timedelta(days=10),
        food_preference="veg",
        smoking="no",
        drinking="no",
        sleep_schedule="night_owl",
        cleanliness="very_clean",
        study_habits="quiet",
    )
    defaults.update(overrides)
    return RoommateProfile.objects.create(user=user, **defaults)


class RoommateProfileTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="u1", password="pass12345")
        self.user2 = User.objects.create_user(username="u2", password="pass12345")

    def test_profile_creation_via_view(self):
        self.client.login(username="u1", password="pass12345")
        resp = self.client.post(reverse("roommates:roommate-create"), {
            "full_name": "Rahul",
            "age": 20,
            "gender": "male",
            "college": "Chandigarh University",
            "preferred_location": "Gharuan",
            "budget_min": 3000,
            "budget_max": 4000,
            "accommodation_type": "pg",
            "sharing_type": "double",
            "move_in_date": (datetime.date.today() + datetime.timedelta(days=5)).isoformat(),
            "food_preference": "non_veg",
            "smoking": "no",
            "drinking": "no",
            "sleep_schedule": "night_owl",
            "cleanliness": "very_clean",
            "study_habits": "quiet",
            "interests": "Music, Football",
            "bio": "Easy-going and clean.",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(RoommateProfile.objects.filter(user=self.user1).exists())

    def test_budget_min_greater_than_max_is_invalid(self):
        from .forms import RoommateProfileForm
        form = RoommateProfileForm(data={
            "full_name": "Rahul", "age": 20, "gender": "male", "college": "X",
            "preferred_location": "Y", "budget_min": 5000, "budget_max": 3000,
            "accommodation_type": "pg", "sharing_type": "double",
            "move_in_date": (datetime.date.today() + datetime.timedelta(days=5)).isoformat(),
            "food_preference": "veg", "smoking": "no", "drinking": "no",
            "sleep_schedule": "night_owl", "cleanliness": "very_clean", "study_habits": "quiet",
        })
        self.assertFalse(form.is_valid())

    def test_visibility_toggle(self):
        profile = make_profile(self.user1)
        self.client.login(username="u1", password="pass12345")
        self.client.post(reverse("roommates:roommate-toggle-visibility"))
        profile.refresh_from_db()
        self.assertFalse(profile.is_active)

    def test_hidden_profile_not_in_list(self):
        make_profile(self.user1, is_active=False)
        resp = self.client.get(reverse("roommates:roommate-list"))
        self.assertNotContains(resp, "Test User")

    def test_user_cannot_edit_another_users_profile(self):
        make_profile(self.user1)
        self.client.login(username="u2", password="pass12345")
        resp = self.client.get(reverse("roommates:roommate-edit"))
        self.assertEqual(resp.status_code, 404)

    def test_match_calculation_returns_percentage(self):
        p1 = make_profile(self.user1)
        p2 = make_profile(self.user2, full_name="User Two")
        score = calculate_match_percentage(p1, p2)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_match_calculation_handles_missing_field_gracefully(self):
        p1 = make_profile(self.user1)
        p2 = make_profile(self.user2, full_name="User Two", preferred_location="")
        score = calculate_match_percentage(p1, p2)
        self.assertIsInstance(score, int)


class ConnectionRequestTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="u1", password="pass12345")
        self.user2 = User.objects.create_user(username="u2", password="pass12345")
        self.profile2 = make_profile(self.user2, full_name="User Two")

    def test_send_request(self):
        self.client.login(username="u1", password="pass12345")
        self.client.post(reverse("roommates:send-roommate-request", args=[self.profile2.pk]))
        self.assertTrue(
            RoommateConnectionRequest.objects.filter(sender=self.user1, receiver=self.user2).exists()
        )

    def test_cannot_send_duplicate_pending_request(self):
        self.client.login(username="u1", password="pass12345")
        self.client.post(reverse("roommates:send-roommate-request", args=[self.profile2.pk]))
        self.client.post(reverse("roommates:send-roommate-request", args=[self.profile2.pk]))
        count = RoommateConnectionRequest.objects.filter(sender=self.user1, receiver=self.user2).count()
        self.assertEqual(count, 1)

    def test_cannot_send_request_to_self(self):
        make_profile(self.user1, full_name="Self")
        self.client.login(username="u1", password="pass12345")
        my_profile = RoommateProfile.objects.get(user=self.user1)
        self.client.post(reverse("roommates:send-roommate-request", args=[my_profile.pk]))
        self.assertFalse(RoommateConnectionRequest.objects.filter(sender=self.user1, receiver=self.user1).exists())

    def test_accept_request(self):
        req = RoommateConnectionRequest.objects.create(sender=self.user1, receiver=self.user2)
        self.client.login(username="u2", password="pass12345")
        self.client.post(reverse("roommates:accept-roommate-request", args=[req.pk]))
        req.refresh_from_db()
        self.assertEqual(req.status, RoommateConnectionRequest.Status.ACCEPTED)

    def test_reject_request(self):
        req = RoommateConnectionRequest.objects.create(sender=self.user1, receiver=self.user2)
        self.client.login(username="u2", password="pass12345")
        self.client.post(reverse("roommates:reject-roommate-request", args=[req.pk]))
        req.refresh_from_db()
        self.assertEqual(req.status, RoommateConnectionRequest.Status.REJECTED)

    def test_unauthorized_user_cannot_accept_request(self):
        req = RoommateConnectionRequest.objects.create(sender=self.user1, receiver=self.user2)
        other_user = User.objects.create_user(username="u3", password="pass12345")
        self.client.login(username="u3", password="pass12345")
        resp = self.client.post(reverse("roommates:accept-roommate-request", args=[req.pk]))
        self.assertEqual(resp.status_code, 404)
