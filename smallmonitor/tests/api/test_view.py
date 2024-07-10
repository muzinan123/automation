# Create your tests here
import json
from api.models import Group, App
from tests import MonitoringTest


class ViewTest(MonitoringTest):

    def test_url_api_groups(self):
        url = '/api/groups/'
        response = self.client.get(url)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(len(data), 3)

        self.assertEquals(data[0]["unique_name"], "youku")
        self.assertEquals(data[0]["display_name"], "Youku")

        self.assertEquals(data[1]["unique_name"], "tudou")
        self.assertEquals(data[1]["display_name"], "Tudou")

        self.assertEquals(data[2]["unique_name"], "aiqiyi")
        self.assertEquals(data[2]["display_name"], "Aiqiyi")

        post_group = {'unique_name': 'postGroup',
                      "display_name": 'postGroup'}
        response = self.client.post(url, post_group, format='json')
        group = Group.objects.filter(unique_name=post_group["unique_name"]).first()
        self.assertEquals(post_group["display_name"], group.display_name)