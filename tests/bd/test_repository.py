# import pytest
#
# from src.bd.repository import Repository, Subscription
#
# pytestmark = pytest.mark.asyncio
#
#
# @pytest.fixture
# def repository() -> Repository:
#     """Фикстура для создания чистого экземпляра Repository."""
#     repo = Repository()
#     yield repo
#     repo.users = {}
#
#
# @pytest.mark.parametrize(
#     ("users", "expected_is_added", "expected_res"),
#     [
#         ({}, True, {123: []}),
#         ({123: []}, False, {123: []}),
#         ({1: []}, True, {1: [], 123: []}),
#     ],
#     ids=["first_user", "existing_user", "new_user"],
# )
# async def test_add_user(
#     repository: Repository,
#     users: dict[int, list[Subscription]],
#     expected_is_added: bool,
#     expected_res: dict[int, list[Subscription]],
# ) -> None:
#     """Проверяет добавление нового пользователя."""
#     repository.users = users
#
#     result = await repository.add_user(123)
#
#     assert result is expected_is_added
#     assert repository.users == expected_res
#
#
# @pytest.mark.parametrize(
#     ("users", "expected_is_added", "expected_result"),
#     [
#         ({}, False, {}),
#         ({1: []}, False, {1: []}),
#         ({123: []}, True, {123: [Subscription(url="https://example.com")]}),
#         (
#             {123: [Subscription(url="https://hello.com")]},
#             True,
#             {123: [Subscription(url="https://hello.com"), Subscription(url="https://example.com")]},
#         ),
#         (
#             {123: [Subscription(url="https://example.com", tags=["work"])]},
#             False,
#             {123: [Subscription(url="https://example.com", tags=["work"])]},
#         ),
#     ],
#     ids=["no_users", "wrong_user", "first_subscription", "new_subscription", "same_url"],
# )
# async def test_add_subscription(
#     repository: Repository,
#     users: dict[int, list[Subscription]],
#     expected_is_added: bool,
#     expected_result: dict[int, list[Subscription]],
# ) -> None:
#     """Проверяет добавление подписки для пользователя."""
#     repository.users = users
#     user_id = 123
#     subscription = Subscription(url="https://example.com")
#
#     result = await repository.add_subscription(user_id, subscription)
#
#     assert result is expected_is_added
#     assert repository.users == expected_result
#
#
# @pytest.mark.parametrize(
#     ("users", "expected_result"),
#     [
#         ({}, {}),
#         (
#             {1: [Subscription(url="https://example.com")]},
#             {1: [Subscription(url="https://example.com")]},
#         ),
#         ({123: []}, {123: []}),
#         (
#             {
#                 1: [Subscription(url="https://example.com")],
#                 123: [
#                     Subscription(url="https://hello.com"),
#                     Subscription(url="https://example.com"),
#                 ],
#             },
#             {
#                 1: [Subscription(url="https://example.com")],
#                 123: [Subscription(url="https://hello.com")],
#             },
#         ),
#         ({123: [Subscription(url="https://example.com", tags=["work"])]}, {123: []}),
#     ],
#     ids=["no_users", "wrong_user", "no_subscription", "same_subscription", "same_url"],
# )
# async def test_remove_subscription(
#     repository: Repository,
#     users: dict[int, list[Subscription]],
#     expected_result: dict[int, list[Subscription]],
# ) -> None:
#     """Проверяет удаление подписки пользователя."""
#     repository.users = users
#     user_id = 123
#     url = "https://example.com"
#
#     await repository.remove_subscription(user_id, url)
#
#     assert repository.users == expected_result
#
#
# @pytest.mark.parametrize(
#     ("users", "expected_result"),
#     [
#         ({}, []),
#         ({1: [Subscription(url="https://example.com")]}, []),
#         ({123: []}, []),
#         (
#             {
#                 1: [Subscription(url="https://example.com")],
#                 123: [
#                     Subscription(url="https://hello.com"),
#                     Subscription(url="https://example.com"),
#                 ],
#             },
#             [Subscription(url="https://hello.com"), Subscription(url="https://example.com")],
#         ),
#         (
#             {123: [Subscription(url="https://example.com", tags=["work"])]},
#             [Subscription(url="https://example.com", tags=["work"])],
#         ),
#     ],
#     ids=["no_users", "wrong_user", "no_subscription", "same_subscription", "same_url"],
# )
# async def test_get_subscription(
#     repository: Repository,
#     users: dict[int, list[Subscription]],
#     expected_result: list[Subscription],
# ) -> None:
#     """Проверяет получение списка подписок пользователя."""
#     repository.users = users
#     user_id = 123
#
#     result = await repository.get_subscriptions(user_id)
#
#     assert result == expected_result
#
#
# @pytest.mark.parametrize(
#     ("users", "expected_result"),
#     [
#         ({}, False),
#         ({1: [Subscription(url="https://example.com")]}, False),
#         ({123: []}, False),
#         (
#             {
#                 1: [Subscription(url="https://example.com")],
#                 123: [
#                     Subscription(url="https://hello.com"),
#                     Subscription(url="https://example.com"),
#                 ],
#             },
#             True,
#         ),
#         ({123: [Subscription(url="https://example.com", tags=["work"])]}, True),
#     ],
#     ids=["no_users", "wrong_user", "no_subscription", "same_subscription", "same_url"],
# )
# async def test_is_user_have_url(
#     repository: Repository,
#     users: dict[int, list[Subscription]],
#     expected_result: bool,
# ) -> None:
#     """Проверяет наличие подписки y пользователя."""
#     repository.users = users
#     user_id = 123
#     url = "https://example.com"
#
#     result = await repository.is_user_have_url(user_id, url)
#
#     assert result == expected_result
