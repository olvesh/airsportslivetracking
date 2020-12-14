from rest_framework_nested import routers

from display.views import ContestViewSet, ImportFCNavigationTask, NavigationTaskViewSet, ContestantViewSet, \
    RouteViewSet, ContestantTrackViewSet
from django.urls import path, include

router = routers.DefaultRouter()
router.register(r'contests', ContestViewSet, basename="contests")
# router.register(r'navigationtasks', NavigationTaskNestedViewSet, basename="rootnavigationtasks")
# router.register(r'routes', RouteViewSet, basename="routes")
router.register(r'tracks', ContestantTrackViewSet, basename="tracks")

navigation_task_router = routers.NestedSimpleRouter(router, r'contests', lookup="contest")
navigation_task_router.register(r'importnavigationtask', ImportFCNavigationTask, basename="importnavigationtask")
navigation_task_router.register(r'navigationtasks', NavigationTaskViewSet, basename="navigationtasks")

contestant_router = routers.NestedSimpleRouter(navigation_task_router, r'navigationtasks', "navigationtasks",
                                               lookup="navigationtask")
contestant_router.register(r'contestants', ContestantViewSet, basename='contestants')

urlpatters = [
    path('', include(router.urls)),
    path('', include(navigation_task_router.urls)),
    path('', include(contestant_router.urls))
]
