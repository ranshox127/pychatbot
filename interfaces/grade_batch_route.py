from flask import Blueprint
from dependency_injector.wiring import inject, Provide
from containers import AppContainer

from application.summary_usecases.grade_batch import GradeBatchUseCase

grade_batch_bp = Blueprint('grade_batch', __name__)


@grade_batch_bp.route("/send_menu/<string:context_title>/<string:contents_name>/", methods=['POST', 'GET'])
@inject
def send_menu(context_title: str, contents_name: str, grade_batch_use_case: GradeBatchUseCase = Provide[AppContainer.grade_batch_use_case]):
    """
    一鍵幫所有學生的summary評分、GAI生成summary回饋、傳送課堂總結表單
    可能讓人混淆的地方: 課堂總結表單的「獲取評分資訊」與「總結回饋」是兩回事
        - 「獲取評分資訊」範例: 同學你好，你的C4總結評分為 [通過]，寫得很棒，請繼續保持喔!
        - 「總結回饋」範例: 以下是C1總結的回饋
    """
    grade_batch_use_case.exec(context_title, contents_name)
    return {'reply': 'OK'}
