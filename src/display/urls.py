from django.urls import path

from display.views import (
    frontend_view_map,
    renew_token,
    NavigationTaskDetailView,
    ContestantUpdateView,
    ContestantCreateView,
    ContestantGateTimesView,
    ContestCreateView,
    ContestUpdateView,
    ContestantDeleteView,
    ContestDeleteView,
    NavigationTaskDeleteView,
    ContestTeamList,
    remove_team_from_contest,
    TeamUpdateView,
    PersonUpdateView,
    PersonList,
    NavigationTaskUpdateView,
    ContestTeamTrackingUpdate,
    manifest,
    tracking_qr_code_view,
    get_contestant_map,
    get_navigation_task_map,
    add_contest_teams_to_navigation_task,
    clear_future_contestants,
    render_contestants_timeline,
    ContestDetailView,
    list_contest_permissions,
    add_user_contest_permissions,
    delete_user_contest_permissions,
    change_user_contest_permissions,
    contestant_cards_list,
    contestant_card_remove,
    create_route_test,
    clear_results_service,
    delete_score_item,
    terminate_contestant_calculator,
    view_navigation_task_rules,
    frontend_playback_map,
    share_contest,
    share_navigation_task,
    get_contestant_default_map,
    get_contestant_email_flight_orders_link,
    EditableRouteList,
    EditableRouteDeleteView,
    refresh_editable_route_navigation_task,
    get_contestant_email_flying_orders_link,
    upload_gpx_track_for_contesant,
    healthz,
    readyz,
    revert_uploaded_gpx_track_for_contestant,
    copy_editable_route,
    download_gpx_track_contestant,
    view_contest_team_images,
    clear_profile_image_background,
    upload_profile_picture,
    get_contestant_processing_statistics,
    get_contest_creators_emails,
    navigation_task_view_detailed_score,
    navigation_task_restore_original_scorecard_view,
    navigation_task_scorecard_override_view,
    navigation_task_gatescore_override_view,
    update_flight_order_configurations,
    UserUploadedMapCreate,
    UserUploadedMapList,
    UserUploadedMapUpdate,
    UserUploadedMapDelete,
    restart_contestant_calculator,
    download_navigation_task_orders,
    generatenavigation_task_orders_template,
    delete_user_useruploadedmap_permissions,
    change_user_useruploadedmap_permissions,
    add_user_useruploadedmap_permissions,
    list_useruploadedmap_permissions,
    WelcomeEmailExample,
    ContestCreationEmailExample,
    list_editableroute_permissions,
    add_user_editableroute_permissions,
    change_user_editableroute_permissions,
    delete_user_editableroute_permissions,
    StatisticsView,
    import_route,
    delete_user_and_person,
    user_start_request_profile_deletion,
    user_request_profile_deletion,
)
from display.views_wizards import NewNavigationTaskWizard, RouteToTaskWizard, RegisterTeamWizard

urlpatterns = [
    path("healthz/", healthz),
    path("readyz/", readyz),
    path("statistics/", StatisticsView.as_view(), name="statistics"),
    path("task/<int:pk>/map/", frontend_view_map, name="frontend_view_map"),
    path("task/<int:pk>/playbackmap/", frontend_playback_map, name="frontend_playback_map"),
    path("useruploadedmaps/", UserUploadedMapList.as_view(), name="useruploadedmap_list"),
    path("useruploadedmaps/create/", UserUploadedMapCreate.as_view(), name="useruploadedmap_add"),
    path("useruploadedmaps/<int:pk>/update/", UserUploadedMapUpdate.as_view(), name="useruploadedmap_change"),
    path("useruploadedmaps/<int:pk>/delete/", UserUploadedMapDelete.as_view(), name="useruploadedmap_delete"),
    path(
        "useruploadedmaps/<int:pk>/permissions/",
        list_useruploadedmap_permissions,
        name="useruploadedmap_permissions_list",
    ),
    path(
        "useruploadedmaps/<int:pk>/permissions/add/",
        add_user_useruploadedmap_permissions,
        name="useruploadedmap_permissions_add",
    ),
    path(
        "useruploadedmaps/<int:pk>/permissions/<int:user_pk>/change/",
        change_user_useruploadedmap_permissions,
        name="useruploadedmap_permissions_change",
    ),
    path(
        "useruploadedmaps/<int:pk>/permissions/<int:user_pk>/delete",
        delete_user_useruploadedmap_permissions,
        name="useruploadedmap_permissions_delete",
    ),
    path("token/renew", renew_token, name="renewtoken"),
    path("users/delete/", delete_user_and_person, name="user_delete"),
    path("users/emails/", get_contest_creators_emails, name="user_emails"),
    path("users/welcomeexample/", WelcomeEmailExample.as_view(), name="welcome_example"),
    path("users/contestexample/", ContestCreationEmailExample.as_view(), name="contestcreation_example"),
    path("contest/create/", ContestCreateView.as_view(), name="contest_create"),
    path("contest/<int:pk>/", ContestDetailView.as_view(), name="contest_details"),
    path("contest/<int:pk>/clear_results/", clear_results_service, name="contest_clear_results"),
    path("contest/<int:pk>/contest_team_images/", view_contest_team_images, name="contest_team_images"),
    path(
        "contest/<int:contest_pk>/remove_image_background/<int:pk>/",
        clear_profile_image_background,
        name="clear_profile_image_background",
    ),
    path(
        "contest/<int:contest_pk>/upload_profile_picture/<int:pk>/",
        upload_profile_picture,
        name="upload_profile_picture",
    ),
    path("contest/<int:pk>/permissions/", list_contest_permissions, name="contest_permissions_list"),
    path("contest/<int:pk>/permissions/add/", add_user_contest_permissions, name="contest_permissions_add"),
    path(
        "contest/<int:pk>/permissions/<int:user_pk>/change/",
        change_user_contest_permissions,
        name="contest_permissions_change",
    ),
    path(
        "contest/<int:pk>/permissions/<int:user_pk>/delete",
        delete_user_contest_permissions,
        name="contest_permissions_delete",
    ),
    path("contest/<int:pk>/create_route/", create_route_test, name="create_route"),
    path("contest/<int:pk>/delete/", ContestDeleteView.as_view(), name="contest_delete"),
    path("contest/<int:pk>/update/", ContestUpdateView.as_view(), name="contest_update"),
    path("contest/<int:pk>/share/", share_contest, name="contest_share"),
    path("navigationtask/<int:pk>/", NavigationTaskDetailView.as_view(), name="navigationtask_detail"),
    path(
        "navigationtask/<int:pk>/restorescorecard/",
        navigation_task_restore_original_scorecard_view,
        name="navigationtask_restorescorecard",
    ),
    path(
        "navigationtask/<int:pk>/scoredetails/", navigation_task_view_detailed_score, name="navigationtask_scoredetails"
    ),
    path(
        "navigationtask/<int:pk>/flightorderconfiguration/",
        update_flight_order_configurations,
        name="navigationtask_flightorderconfiguration",
    ),
    path(
        "navigationtask/<int:pk>/updatescorecardoverride/",
        navigation_task_scorecard_override_view,
        name="navigationtask_updatescorecardoverride",
    ),
    path(
        "navigationtask/<int:pk>/updategatescoreoverride/<int:gate_score_pk>/",
        navigation_task_gatescore_override_view,
        name="navigationtask_updategatescoreoverride",
    ),
    path("navigationtask/<int:pk>/qr/", tracking_qr_code_view, name="navigationtask_qr"),
    path("navigationtask/<int:pk>/map/", get_navigation_task_map, name="navigationtask_map"),
    path("navigationtask/<int:pk>/rules/", view_navigation_task_rules, name="navigationtask_rules"),
    path("navigationtask/<int:pk>/update/", NavigationTaskUpdateView.as_view(), name="navigationtask_update"),
    path("navigationtask/<int:pk>/delete/", NavigationTaskDeleteView.as_view(), name="navigationtask_delete"),
    path("navigationtask/<int:pk>/share/", share_navigation_task, name="navigationtask_share"),
    path(
        "navigationtask/<int:pk>/flightordersprogress/",
        generatenavigation_task_orders_template,
        name="navigationtask_flightordersprogress",
    ),
    path(
        "navigationtask/<int:pk>/downloadflightorders/",
        download_navigation_task_orders,
        name="navigationtask_downloadflightorders",
    ),
    path(
        "navigationtask/<int:pk>/refresheditableroute/",
        refresh_editable_route_navigation_task,
        name="navigationtask_refresheditableroute",
    ),
    path(
        "navigationtask/<int:pk>/add_contestants/",
        add_contest_teams_to_navigation_task,
        name="navigationtask_addcontestants",
    ),
    path(
        "navigationtask/<int:pk>/remove_contestants/", clear_future_contestants, name="navigationtask_removecontestants"
    ),
    path(
        "navigationtask/<int:pk>/contestants_timeline/",
        render_contestants_timeline,
        name="navigationtask_contestantstimeline",
    ),
    path("maplink/<uuid:key>/", get_contestant_email_flight_orders_link, name="email_map_link"),
    path("mapreport/<int:pk>/", get_contestant_email_flying_orders_link, name="email_report_link"),
    path("contestant/<int:navigationtask_pk>/create/", ContestantCreateView.as_view(), name="contestant_create"),
    path(
        "contestant/<int:pk>/processingstatistics/", get_contestant_processing_statistics, name="processingstatistics"
    ),
    path("contestant/<int:pk>/map/", get_contestant_map, name="contestant_map"),
    path("contestant/<int:pk>/defaultmap/", get_contestant_default_map, name="contestant_default_map"),
    path("contestant/<int:pk>/stop_calculator/", terminate_contestant_calculator, name="contestant_stop_calculator"),
    path(
        "contestant/<int:pk>/restart_calculator/", restart_contestant_calculator, name="contestant_restart_calculator"
    ),
    path("contestant/<int:pk>/list_cards/", contestant_cards_list, name="contestant_cards_list"),
    path("contestant/<int:pk>/remove_card/<int:card_pk>/", contestant_card_remove, name="contestant_card_remove"),
    path("contestant/<int:pk>/update/", ContestantUpdateView.as_view(), name="contestant_update"),
    path("contestant/<int:pk>/delete/", ContestantDeleteView.as_view(), name="contestant_delete"),
    path("contestant/<int:pk>/uploadgpxtrack/", upload_gpx_track_for_contesant, name="contestant_uploadgpxtrack"),
    path("contestant/<int:pk>/downloadgpxtrack/", download_gpx_track_contestant, name="contestant_downloadgpxtrack"),
    path(
        "contestant/<int:pk>/recalculatetraccartrack/",
        revert_uploaded_gpx_track_for_contestant,
        name="contestant_recalculatetraccartrack",
    ),
    # path('contestant/<int:pk>/downloadgpxtrack/', download_gpx_track_for_contesant, name="contestant_downloadgpxtrack"),
    path("contestant/remove_score_item/<int:pk>/", delete_score_item, name="contestant_remove_score_item"),
    path("contestant/<int:pk>/gates/", ContestantGateTimesView.as_view(), name="contestant_gate_times"),
    path("contest/<int:contest_pk>/team/<int:team_pk>/wizardupdate/", RegisterTeamWizard.as_view(), name="team_wizard"),
    path("contest/<int:contest_pk>/team/<int:team_pk>/remove/", remove_team_from_contest, name="remove_team"),
    path("contest/<int:contest_pk>/team/create/", RegisterTeamWizard.as_view(), name="create_team"),
    path("contest/<int:contest_pk>/team/<int:pk>/update", TeamUpdateView.as_view(), name="team_update"),
    path(
        "contest/<int:contest_pk>/contestteamtracking/<int:pk>/update",
        ContestTeamTrackingUpdate.as_view(),
        name="contestteamtracking_update",
    ),
    path("contest/<int:contest_pk>/teams/", ContestTeamList.as_view(), name="contest_team_list"),
    path("navigationtaskwizard/<int:contest_pk>/", NewNavigationTaskWizard.as_view(), name="navigationtaskwizard"),
    path("person/<int:pk>/update/", PersonUpdateView.as_view(), name="person_update"),
    path("person/request_deletion/", user_start_request_profile_deletion, name="user_start_request_profile_deletion"),
    path("person/request_deletion_confirm/", user_request_profile_deletion, name="user_request_profile_deletion"),
    path("person/", PersonList.as_view(), name="person_list"),
    path("manifest/", manifest, name="tracking_manifest"),
    path("editableroute/", EditableRouteList.as_view(), name="editableroute_list"),
    path("editableroute/import/", import_route, name="editableroute_import"),
    path("editableroute/<int:pk>/delete/", EditableRouteDeleteView.as_view(), name="editableroute_delete"),
    path("editableroute/<int:pk>/copy/", copy_editable_route, name="editableroute_copy"),
    path(
        "editableroute/<int:pk>/createnavigationtask/",
        RouteToTaskWizard.as_view(),
        name="editableroute_createnavigationtask",
    ),
    path("editableroute/<int:pk>/permissions/", list_editableroute_permissions, name="editableroute_permissions_list"),
    path(
        "editableroute/<int:pk>/permissions/add/",
        add_user_editableroute_permissions,
        name="editableroute_permissions_add",
    ),
    path(
        "editableroute/<int:pk>/permissions/<int:user_pk>/change/",
        change_user_editableroute_permissions,
        name="editableroute_permissions_change",
    ),
    path(
        "editableroute/<int:pk>/permissions/<int:user_pk>/delete",
        delete_user_editableroute_permissions,
        name="editableroute_permissions_delete",
    ),
]
