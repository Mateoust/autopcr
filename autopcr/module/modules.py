from ..core import pcrclient
from .modulebase import *
from ..model.error import *
from ..core.database import db
from ..model.models import *
import random
from abc import abstractmethod

@description('在公会中自动随机选择一位成员点赞。')
@booltype
@default(True)
class clan_like(Module):
    async def do_task(self, client: pcrclient):
        if not client.data.clan_like_count:
            raise SkipError('今日点赞次数已用完。')
        info = await client.get_clan_info()
        members = [x.viewer_id for x in info.members if x.viewer_id != client.viewer_id]
        if len(members) == 0: raise AbortError("No other members in clan")
        rnd = random.choice(members)
        await client.clan_like(rnd)

@description('使用体力时，若体力不足，最多允许购买的体力管数。')
@enumtype([0, 1, 2, 3, 6, 9, 12])
@default(6)
class buy_stamina_passive(Module):
    async def do_task(self, client: pcrclient):
        client.keys['buy_stamina_passive'] = self.value
     
@description('每天主动购买的体力管数。钻石数量<1w强制不触发。')
@enumtype([0, 1, 2, 3, 6, 9, 12])
@default(0)
class buy_stamina_active(Module):
    async def do_task(self, client: pcrclient):
        for i in range(self.value):
            if client.jewel.free_jewel < 10000:
                raise AbortError('钻石数量不足。中止购买体力。')
            await client.recover_stamina()

@description('收取家园体。')
@booltype
@default(True)
class room_accept_all(Module):
    async def do_task(self, client: pcrclient):
        room = await client.room_start()
        t = client.data.stamina
        for x in room.user_room_item_list:
            if x.item_count:
                await client.room_accept_all()
                return
        self._log(f'收取家园体力：{t} => {client.data.stamina}')
        raise SkipError('没有可收取的家园物品。')

@description('EXP探索和MANA探索。')
@booltype
@default(True)
class explore(Module):
    async def do_task(self, client: pcrclient):
        # 11级探索
        if client.data.training_quest_count.gold_quest:
            self._log(f'Mana探索: {2 - client.data.training_quest_count.gold_quest}次')
            await client.training_quest_skip(21001011, 2 - client.data.training_quest_count.gold_quest)
        else:
            self._log(f'Mana探索：已完成')
        if client.data.training_quest_count.exp_quest:
            self._log(f'Exp探索: {2 - client.data.training_quest_count.exp_quest}次')
            await client.training_quest_skip(21002011, 2 - client.data.training_quest_count.exp_quest)
        else:
            self._log(f'Exp探索：已完成')


@description('领取礼物箱')
@booltype
@default(True)
class present_receive_all(Module):
    async def do_task(self, client: pcrclient):
        present = await client.present_index()
        if not present.present_count:
            raise SkipError("No present to receive")
        await client.present_receive_all()
        self._log('礼物已领取完成')

@description('领取双场币')
@booltype
@default(True)
class jjc_reward(Module):
    async def do_task(self, client: pcrclient):
        info = await client.get_arena_info()
        if info.reward_info.count:
            await client.receive_arena_reward()
            self._log(f'领取jjc币x{info.reward_info.count}')
        else:
            self._log('jjc币已领取完成')
        info = await client.get_grand_arena_info()
        if info.reward_info.count:
            await client.receive_grand_arena_reward()
            self._log(f'领取pjjc币x{info.reward_info.count}')
        else:
            self._log('pjjc币已领取完成')

@description('刷取心碎3')
@booltype
@default(True)
class xinsui3_sweep(Module):
    async def do_task(self, client: pcrclient):
        await client.quest_skip_aware(18001003, 5)
        self._log('心碎3已刷取完成')

@description('刷取心碎2')
@booltype
@default(True)
class xinsui2_sweep(Module):
    async def do_task(self, client: pcrclient):
        await client.quest_skip_aware(18001002, 5)
        self._log('心碎2已刷取完成')

@description('刷取心碎1')
@booltype
@default(True)
class xinsui1_sweep(Module):
    async def do_task(self, client: pcrclient):
        await client.quest_skip_aware(18001001, 5)
        self._log('心碎1已刷取完成')

@description('刷取星球杯2')
@booltype
@default(True)
class xingqiubei2_sweep(Module):
    async def do_task(self, client: pcrclient):
        await client.quest_skip_aware(19001002, 5)
        self._log('星球杯2已刷取完成')

@description('刷取星球杯1')
@booltype
@default(True)
class xingqiubei1_sweep(Module):
    async def do_task(self, client: pcrclient):
        await client.quest_skip_aware(19001001, 5)
        self._log('星球杯1已刷取完成')

@description('''
根据一键扫荡设置自动刷图，具体次数由标签页名字和设置的使用扫荡张数决定
刷图逻辑：首先按次数逐一刷取名字为start的图，然后循环按次数刷取设置为loop的图
当被动体力回复完全消耗后，刷图结束
'''.strip())
@booltype
@default(True)
class smart_sweep(Module):
    async def do_task(self, client: pcrclient):
        nloop = []
        loop = []
        for tab in client.data.user_my_quest:
            for x in tab.skip_list:
                if tab.tab_name == 'start':
                    nloop.append((x, tab.skip_count))
                elif tab.tab_name == 'loop':
                    loop.append((x, tab.skip_count))
        def _sweep():
            for x in nloop:
                yield x
            while True:
                for x in loop:
                    yield x

        for quest_id, count in _sweep():
            try:
                await client.quest_skip_aware(quest_id, count, True, True)
            except SkipError as e:
                m = str(e)
                if m == '体力不足': break
                else:
                    self._log(m)
                    if not m.endswith("已达最大次数"):
                        raise

@description('领取任务奖励')
@booltype
@default(True)
class receive_mission_reward(Module):
    async def do_task(self, client: pcrclient):
        index = await client.mission_index()
        if not [x for x in index.missions if x.mission_status == eMissionStatusType.EnableReceive]:
            raise SkipError("没有要领取的任务奖励")
        await client.mission_receive()
        self._log('任务奖励已领取完成')

@description('领取任务奖励2')
class receive_mission_reward2(receive_mission_reward):
    pass

@description('探索露娜塔回廊')
@booltype
@default(True)
class tower_explore(Module):
    async def do_task(self, client: pcrclient):
        top = await client.get_tower_top()
        if not top.cloister_first_cleared_flag:
            raise AbortError("露娜塔回廊未开启")
        await client.tower_cloister_battle_skip(top.cloister_remain_clear_count)
        self._log('露娜塔回廊已探索完成')

@description('普通扭蛋')
@booltype
@default(True)
class gacha_normal(Module):
    async def do_task(self, client: pcrclient):
        await client.normal_gacha()
        self._log('普通扭蛋已完成')


@description('商店购买最大碎片量')
@enumtype([0, 100, 300, 600, 900, 99999])
@default(300)
class shop_buy_limit(Module):
    async def do_task(self, client: pcrclient):
        client.keys['shop_buy_limit'] = self.value

class shop_buy(Module):
    @abstractmethod
    def system_id(self) -> int: ...
    @abstractmethod
    def coin_limit(self) -> int: ...

    async def _get_shop_content(self, client: pcrclient):
        for shop in (await client.get_shop_item_list()).shop_list:
            if shop.system_id == self.system_id():
                return shop
        raise AbortError("商店未开启")

    async def do_task(self, client: pcrclient):
        shop_content = await self._get_shop_content(client)

        prev = client.data.get_shop_gold(self.system_id())

        while shop_content.reset_count <= self.value:
            slots_to_buy = []
            for item in shop_content.item_list:
                if item.available_num and client.data.get_inventory((item.type, item.item_id)) < self.coin_limit():
                    slots_to_buy.append(item.slot_id)

            if slots_to_buy:
                await client.shop_buy_item(shop_content.system_id, slots_to_buy)

            if shop_content.reset_count == self.value:
                break
            
            if client.data.get_shop_gold(self.system_id()) < self.coin_limit():
                raise AbortError(f"商店金币小于{self.coin_limit()}，无法继续购买")

            await client.shop_reset(shop_content.system_id)
            shop_content = await self._get_shop_content(client)

        self._log(f"已花费{client.data.get_shop_gold(self.system_id()) - prev}代币购买装备")

@description('购买地下城币刷新次数, -1为不购买')
@enumtype([-1, 0, 1, 2, 3, 4, 7, 10])
@default(0)
class dungeon_shop(shop_buy):
    def system_id(self) -> int:
        return 204
    def coin_limit(self) -> int:
        return 100000

@description('购买jjc币刷新次数, -1为不购买')
@enumtype([-1, 0, 1, 2, 3, 4, 7, 10])
@default(0)
class jjc_shop(shop_buy):
    def system_id(self) -> int:
        return 202
    def coin_limit(self) -> int:
        return 100000

@description('购买pjjc币刷新次数, -1为不购买')
@enumtype([-1, 0, 1, 2, 3, 4, 7, 10])
@default(0)
class pjjc_shop(shop_buy):
    def system_id(self) -> int:
        return 203
    def coin_limit(self) -> int:
        return 100000


def register_test():
    ModuleManager._modules = [
        buy_stamina_passive,
        smart_sweep
    ]

def register_all():
    ModuleManager._modules = [
        buy_stamina_passive,
        receive_mission_reward,
        clan_like,
        room_accept_all,
        explore,
        gacha_normal,
        dungeon_shop,
        jjc_shop,
        pjjc_shop,
        dungeon_sweep,
        sixstar_sweep,
        hatsune135_sweep,
        hatsune24_sweep,
        jjc_reward,
        tower_explore,
        xinsui3_sweep,
        xinsui2_sweep,
        xingqiubei2_sweep,
        xinsui1_sweep,
        xingqiubei1_sweep,
        hatsune_hboss_sweep,
        hatsune_present_receive_all,
        hatsune_exchange,
        daily_shop,
        buy_stamina_active,
        present_receive_all,
        smart_sweep,
        receive_mission_reward2,
    ]