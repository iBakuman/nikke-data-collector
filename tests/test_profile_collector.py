from collector.profile_collector import ProfileCollector


def test_profile_collector(profile_collector: ProfileCollector):
    user = profile_collector.collect()
    user.save_profile_image("testdata/profile_collector")
    user.save_team_image("testdata/profile_collector")

