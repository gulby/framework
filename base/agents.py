class Agent(object):
    class Meta:
        proxy = True

    # class part
    is_agent = True
    _instance = None

    def __str__(self):
        cls_name = self.__class__.__name__
        return cls_name.replace("Agent", "")

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def get_master(self, context):
        raise NotImplementedError


class DummyAgent(Agent):
    class Meta:
        proxy = True

    def get_master(self, context):
        # 이는 샘플일 뿐이고 실제 구현에서는 context 의 속성 중 적절한 것을 리턴
        return context
