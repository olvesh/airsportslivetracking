import React, {Component} from "react";

export default class AccumulatedScore extends Component {
    render() {
        return  <div className={"danger-level-accumulated-score-container"}>
            <img src={"/static/img/gate_score_arrow_red.gif"} style={{width:"100%"}}/>
            <div className={"danger-level-accumulated-score"}>
                {this.props.value}
            </div>
        </div>
    }
}