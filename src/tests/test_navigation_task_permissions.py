import datetime

from django.contrib.auth.models import User, Permission
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from display.models import Contest, NavigationTask

line = {
    "name": "land",
    "latitude": 0,
    "longitude": 0,
    "elevation": 0,
    "width": 1,
    "gate_line": [],
    "end_curved": False,
    "is_procedure_turn": False,
    "time_check": True,
    "gate_check": True,
    "planning_test": True,
    "type": "TP",
    "distance_next": 0,
    "bearing_next": 0,
    "distance_previous": 0,
    "bearing_from_previous": 0

}

NAVIGATION_TASK_DATA = {"name": "Task", "start_time": datetime.datetime.utcnow(),
                        "finish_time": datetime.datetime.utcnow(), "route": {
        "waypoints": [],
        "starting_line": line,
        "takeoff_gate": line,
        "landing_gate": line,
        "name": "name"
    }}


class TestCreateNavigationTask(APITestCase):
    def setUp(self):
        self.user_owner = User.objects.create(username="withpermissions")
        permission = Permission.objects.get(codename="add_contest")
        self.user_owner.user_permissions.add(permission)
        self.user_without_permissions = User.objects.create(username="withoutpermissions")
        self.client.force_login(user=self.user_owner)
        result = self.client.post(reverse("contests-list"), data={"name": "TestContest", "is_public": False})
        print(result.json())
        self.contest_id = result.json()["id"]
        self.contest = Contest.objects.get(pk=self.contest_id)

    def test_create_navigation_task_without_login(self):
        self.client.logout()
        result = self.client.post(reverse("navigationtasks-list", kwargs={"contest_pk": self.contest_id}),
                                  data=NAVIGATION_TASK_DATA, format="json")
        print(result)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_navigation_task_without_privileges(self):
        self.client.force_login(user=self.user_without_permissions)
        result = self.client.post(reverse("navigationtasks-list", kwargs={"contest_pk": self.contest_id}),
                                  data=NAVIGATION_TASK_DATA, format="json")
        print(result)
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_navigation_task_with_privileges(self):
        self.client.force_login(user=self.user_owner)
        result = self.client.post(reverse("navigationtasks-list", kwargs={"contest_pk": self.contest_id}),
                                  data=NAVIGATION_TASK_DATA, format="json")
        print(result)
        print(result.content)
        self.assertEqual(result.status_code, status.HTTP_200_OK)


class TestAccessNavigationTask(APITestCase):
    def setUp(self):
        self.user_owner = User.objects.create(username="withpermissions")
        self.user_owner.user_permissions.add(Permission.objects.get(codename="add_contest"),
                                             Permission.objects.get(codename="change_contest"))
        self.user_someone_else = User.objects.create(username="withoutpermissions")
        self.client.force_login(user=self.user_owner)
        result = self.client.post(reverse("contests-list"), data={"name": "TestContest", "is_public": False})
        print(result.json())
        self.contest_id = result.json()["id"]
        self.contest = Contest.objects.get(pk=self.contest_id)
        result = self.client.post(reverse("navigationtasks-list", kwargs={"contest_pk": self.contest_id}),
                                  data=NAVIGATION_TASK_DATA, format="json")
        print(result.content)
        self.navigation_task = NavigationTask.objects.get(pk=result.json()["id"])

    def test_put_navigation_task_without_login(self):
        self.client.logout()
        data = dict(NAVIGATION_TASK_DATA)
        data["name"] = "Putting a new name"

        result = self.client.put(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}),
            data=data, format="json")
        print(result)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_navigation_task_as_someone_else(self):
        self.client.force_login(user=self.user_someone_else)
        data = dict(NAVIGATION_TASK_DATA)
        data["name"] = "Putting a new name"

        result = self.client.put(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}),
            data=data, format="json")
        print(result)
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_navigation_task_as_creator(self):
        self.client.force_login(user=self.user_owner)
        data = dict(NAVIGATION_TASK_DATA)
        data["name"] = "Putting a new name"
        result = self.client.put(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}),
            data=data, format="json")
        print(result)
        print(result.content)
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_navigation_task_without_login(self):
        self.client.logout()
        data = {"name": "Putting a new name"}

        result = self.client.patch(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}),
            data=data, format="json")
        print(result)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_navigation_task_as_someone_else(self):
        self.client.force_login(user=self.user_someone_else)
        data = {"name": "Putting a new name"}
        result = self.client.patch(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}),
            data=data, format="json")
        print(result)
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_navigation_task_as_creator(self):
        self.client.force_login(user=self.user_owner)
        data = {"name": "Putting a new name"}
        result = self.client.patch(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}),
            data=data, format="json")
        print(result)
        print(result.content)
        self.assertEqual(result.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_publish_navigation_task_without_login(self):
        self.client.logout()
        result = self.client.put(
            reverse("navigationtasks-publish", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}))
        print(result)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_publish_navigation_task_as_someone_else(self):
        self.client.force_login(user=self.user_someone_else)
        result = self.client.put(
            reverse("navigationtasks-publish", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}))
        print(result)
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_publish_navigation_task_as_creator(self):
        self.client.force_login(user=self.user_owner)
        result = self.client.put(
            reverse("navigationtasks-publish", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}))
        print(result)
        print(result.content)
        self.assertEqual(result.status_code, status.HTTP_200_OK)

    def test_view_navigation_task_without_login(self):
        self.client.logout()
        result = self.client.get(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}))
        print(result)
        self.assertEqual(result.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_navigation_task_as_someone_else(self):
        self.client.force_login(user=self.user_someone_else)
        result = self.client.get(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}))
        print(result)
        self.assertEqual(result.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_navigation_task_as_creator(self):
        self.client.force_login(user=self.user_owner)
        result = self.client.get(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}))
        print(result)
        print(result.content)
        self.assertEqual(result.status_code, status.HTTP_200_OK)

    def test_view_public_navigation_task_without_login(self):
        self.contest.is_public = True
        self.contest.save()
        self.navigation_task.is_public = True
        self.navigation_task.save()
        self.client.logout()
        result = self.client.get(reverse("contests-detail", kwargs={'pk': self.contest_id}),
                                 data={"name": "TestContest2"})
        print(result)
        self.assertEqual(result.status_code, status.HTTP_200_OK)

    def test_view_public_navigation_task_as_someone_else(self):
        self.contest.is_public = True
        self.contest.save()
        self.navigation_task.is_public = True
        self.navigation_task.save()
        self.client.logout()
        self.client.force_login(user=self.user_someone_else)
        result = self.client.get(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}))
        print(result)
        self.assertEqual(result.status_code, status.HTTP_200_OK)

    def test_view_public_navigation_task_as_creator(self):
        self.contest.is_public = True
        self.contest.save()
        self.navigation_task.is_public = True
        self.navigation_task.save()
        self.client.logout()
        self.client.force_login(user=self.user_owner)
        result = self.client.get(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}))
        print(result)
        print(result.content)
        self.assertEqual(result.status_code, status.HTTP_200_OK)

    def test_view_public_contest_hidden_navigation_task_navigation_task_without_login(self):
        self.contest.is_public = True
        self.contest.save()
        self.navigation_task.is_public = False
        self.navigation_task.save()
        self.client.logout()
        result = self.client.get(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}))

        print(result)
        self.assertEqual(result.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_hidden_contest_public_navigation_task_navigation_task_without_login(self):
        self.contest.is_public = False
        self.contest.save()
        self.navigation_task.is_public = True
        self.navigation_task.save()
        self.client.logout()
        result = self.client.get(
            reverse("navigationtasks-detail", kwargs={'contest_pk': self.contest_id, 'pk': self.navigation_task.id}))
        print(result)
        self.assertEqual(result.status_code, status.HTTP_404_NOT_FOUND)
