"""Generate the original, deterministic supermarket practice dataset."""

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path


START = date(2025, 3, 1)
END = date(2025, 3, 30)
SEED = 20250330

# name, sales unit, price per unit (CNY), typical units sold per day
CATALOG = {
    "蔬菜": [
        ("上海青", "千克", 7.60, 16), ("西红柿", "千克", 9.80, 19),
        ("黄瓜", "千克", 6.80, 12), ("胡萝卜", "千克", 4.90, 10),
        ("西兰花", "千克", 12.50, 8), ("紫甘蓝", "千克", 7.90, 7),
        ("杏鲍菇", "千克", 15.80, 8), ("白萝卜", "千克", 3.90, 12),
        ("甜玉米", "件", 4.50, 14), ("香葱", "千克", 17.60, 4),
    ],
    "水果": [
        ("红富士苹果", "千克", 13.60, 18), ("香蕉", "千克", 9.80, 17),
        ("无籽葡萄", "千克", 32.80, 10), ("蜜橘", "千克", 11.80, 15),
        ("雪梨", "千克", 9.90, 11), ("草莓盒装", "件", 22.90, 12),
        ("猕猴桃", "件", 4.50, 19), ("蓝莓盒装", "件", 16.90, 8),
        ("芒果", "千克", 19.90, 9), ("柠檬", "件", 3.50, 6),
    ],
    "肉蛋水产": [
        ("鲜鸡蛋盒装", "件", 15.90, 23), ("鸡胸肉", "千克", 25.80, 12),
        ("猪里脊", "千克", 38.80, 8), ("五花肉", "千克", 34.80, 12),
        ("牛腱", "千克", 75.00, 6), ("虾仁盒装", "件", 28.90, 7),
        ("鲈鱼", "千克", 39.90, 5), ("鸡翅中", "千克", 38.80, 9),
        ("鹌鹑蛋盒装", "件", 11.90, 8), ("黑鱼片", "千克", 32.50, 6),
    ],
    "乳品冷藏": [
        ("鲜牛奶", "升", 17.90, 25), ("原味酸奶", "件", 13.90, 19),
        ("无糖豆乳", "升", 12.90, 13), ("儿童奶酪棒", "件", 25.90, 12),
        ("盒装嫩豆腐", "件", 3.90, 22), ("无盐黄油", "件", 29.90, 5),
        ("酸奶饮品", "升", 18.90, 11), ("冰鲜面条", "件", 6.90, 13),
        ("芝士片", "件", 19.90, 7), ("淡奶油", "升", 59.90, 4),
    ],
    "粮油调味": [
        ("东北大米", "千克", 8.90, 24), ("花生油", "升", 32.90, 12),
        ("低钠生抽", "升", 26.90, 7), ("陈醋", "升", 17.90, 7),
        ("鸡蛋挂面", "件", 8.90, 13), ("糯米", "千克", 11.90, 9),
        ("全麦面粉", "千克", 10.90, 8), ("火锅底料", "件", 17.90, 8),
        ("黑芝麻酱", "件", 15.90, 3), ("香料礼盒", "件", 39.90, 3),
    ],
    "休闲饮料": [
        ("无糖乌龙茶", "件", 5.50, 23), ("原味苏打水", "件", 4.90, 15),
        ("橙汁", "升", 16.90, 12), ("纯净水", "件", 2.50, 28),
        ("海盐饼干", "件", 12.90, 11), ("低糖燕麦棒", "件", 9.90, 8),
        ("每日坚果", "件", 29.90, 8), ("黑巧克力", "件", 15.90, 8),
        ("草莓果冻", "件", 7.90, 10), ("薯片组合装", "件", 13.90, 14),
    ],
}

# A late inbound shipment leaves these products with no replenishment on the last day.
DELAYED_RECEIPTS = {"S002", "S006", "S013", "S019", "S022", "S031", "S041", "S054"}
PROMOTED = {"S011", "S012", "S014", "S016", "S018", "S032", "S035", "S038"}
COUNT_DIFFERENCES = {"S002": 2, "S006": 2, "S012": -3, "S025": 2, "S035": -1, "S053": -2}


def generate():
    rng = random.Random(SEED)
    products = []
    daily = []
    dates = [START + timedelta(days=offset) for offset in range((END - START).days + 1)]

    for category, items in CATALOG.items():
        for name, unit, price, base_demand in items:
            sku = f"S{len(products) + 1:03d}"
            products.append({"sku": sku, "name": name, "category": category, "unit": unit})
            stock = 2 * base_demand
            for day in dates:
                weekend = 1.22 if day.weekday() >= 5 else 1.0
                promotion = sku in PROMOTED and day >= date(2025, 3, 24)
                demand = round(base_demand * weekend * rng.uniform(0.66, 1.29) * (1.32 if promotion else 1))
                if sku == "S050" and day >= date(2025, 3, 24):
                    demand = 0  # An end-of-season gift set with remaining stock.

                cover_target = 2.1 if category in {"蔬菜", "水果", "乳品冷藏"} else 3.4
                if stock <= 1.3 * base_demand:
                    if day != END or sku not in DELAYED_RECEIPTS:
                        stock = round(cover_target * base_demand * rng.uniform(0.92, 1.12))

                quantity = min(stock, demand)
                stock -= quantity
                revenue = round(quantity * price * (0.92 if promotion else 1), 2)

                physical_count = None
                if day == END and ((len(products) - 1) % 3 == 0 or sku in COUNT_DIFFERENCES):
                    physical_count = max(0, stock + COUNT_DIFFERENCES.get(sku, 0))
                daily.append([day.isoformat(), sku, quantity, revenue, stock, physical_count])

    daily.sort(key=lambda row: (row[0], row[1]))
    return {
        "products": products,
        "daily": daily,
        "provenance": (
            "项目独立生成的模拟超市样本，固定随机种子 20250330。"
            "卡内基梅隆大学 MLIP 的公开案例仅提供业务场景参考。"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("report_data.json"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(generate(), ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
