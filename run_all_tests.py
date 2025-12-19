"""
运行所有测试脚本

按顺序执行所有测试用例：
1. 测试 1：网络数据捕获
2. 测试 2：Tab 管理
3. 测试 3：DOM 可见性检查
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from tests.test_1 import test_network_capture
from tests.test_2 import test_simple_tab_management
from tests.test_3 import test_dom_visibility


async def run_all_tests():
    """运行所有测试"""
    print("=" * 80)
    print("🚀 开始运行所有测试")
    print("=" * 80)
    print()

    tests = [
        ("测试 1：网络数据捕获", test_network_capture),
        ("测试 2：Tab 管理", test_simple_tab_management),
        ("测试 3：DOM 可见性检查", test_dom_visibility),
    ]

    results = []

    for i, (test_name, test_func) in enumerate(tests, 1):
        print(f"\n{'=' * 80}")
        print(f"📝 [{i}/{len(tests)}] {test_name}")
        print(f"{'=' * 80}\n")

        try:
            await test_func()
            results.append((test_name, "✅ 通过"))
            print(f"\n✅ {test_name} - 完成")
        except Exception as e:
            results.append((test_name, f"❌ 失败: {str(e)}"))
            print(f"\n❌ {test_name} - 失败")
            print(f"错误: {e}")

        # 测试之间等待，确保资源清理
        if i < len(tests):
            print(f"\n⏳ 等待 3 秒后继续下一个测试...\n")
            await asyncio.sleep(3)

    # 输出测试结果汇总
    print("\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)

    for test_name, result in results:
        print(f"{result:30s} - {test_name}")

    print("=" * 80)

    # 统计
    passed = sum(1 for _, r in results if r.startswith("✅"))
    failed = sum(1 for _, r in results if r.startswith("❌"))

    print(f"\n总计: {len(results)} 个测试")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
