from fastapi import APIRouter

from freqtrade.rpc.api_server.api_schemas import (
    AutoTradePanelConfig,
    AutoTradePanelConfigPayload,
    StatusMsg,
)
from freqtrade.rpc.api_server.autotrade import AutoTradeManager


router = APIRouter()
_manager = AutoTradeManager()


@router.get("/autotrade/panel", response_model=AutoTradePanelConfig, tags=["Trading"])
def get_autotrade_panel():
    return _manager.get_state()


@router.put("/autotrade/panel", response_model=AutoTradePanelConfig, tags=["Trading"])
def update_autotrade_panel(payload: AutoTradePanelConfigPayload):
    return _manager.update_config(payload.model_dump())


@router.post("/autotrade/start", response_model=AutoTradePanelConfig, tags=["Trading"])
def start_autotrade():
    return _manager.start()


@router.post("/autotrade/stop", response_model=AutoTradePanelConfig, tags=["Trading"])
def stop_autotrade():
    return _manager.stop()


@router.post("/autotrade/run-now", response_model=AutoTradePanelConfig, tags=["Trading"])
def autotrade_run_now():
    return _manager.run_now()


@router.get("/autotrade/demo-disclaimer", response_model=StatusMsg, tags=["Trading"])
def autotrade_demo_disclaimer():
    return {
        "status": (
            "Integração em modo demo habilitada. Configure credenciais de sandbox no exchange "
            "e execute primeiro em dry-run antes de usar conta real."
        )
    }
