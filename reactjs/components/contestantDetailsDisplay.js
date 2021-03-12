import React, {Component} from "react";
import {connect} from "react-redux";
import {
    calculateProjectedScore,
    compareScore,
    contestantShortForm,
    contestantTwoLines,
    ordinal_suffix_of
} from "../utilities";
import paginationFactory from "react-bootstrap-table2-paginator";
import BootstrapTable from "react-bootstrap-table-next";
import "bootstrap/dist/css/bootstrap.min.css"
import {Loading} from "./basicComponents";
import {ProgressCircle} from "./contestantProgress";
import {SIMPLE_RANK_DISPLAY} from "../constants/display-types";
import {displayAllTracks, hideLowerThirds, setDisplay} from "../actions";

const mapStateToProps = (state, props) => ({
    contestantData: state.contestantData[props.contestantId] !== undefined ? state.contestantData[props.contestantId].contestant_track : null,
    initialLoading: state.initialLoadingContestantData[props.contestantId],
    progress: state.contestantData[props.contestantId].progress,
    contestant: state.contestants[props.contestantId],
    contestants: Object.keys(state.contestantData).map((key, index) => {
        return {
            track: state.contestantData[key].contestant_track,
            contestant: state.contestants[key]
        }
    }),
})

function FormatMessage(props) {
    const message = props.message
    let string = message.points.toFixed(2) + " points for " + message.message;
    let offset_string = null
    if (message.offset_string != null) {
        offset_string = " (" + message.offset_string + ")"
    }
    let times = null
    if (message.planned != null && message.actual != null) {
        times = "\n(planned: " + message.planned + ", actual: " + message.actual + ")"
    }
    return <div className={"preWrap"}>{message.points.toFixed(2)} points {message.message} {offset_string}<span
        className={"gateTimesText"}>{times}</span></div>
}

class ConnectedContestantDetailsDisplay extends Component {
    constructor(props) {
        super(props)
    }

    calculateRank() {
        const contestants = this.props.contestants.filter((contestant) => {
            return contestant != null && contestant.contestant !== undefined
        })
        contestants.sort(compareScore)
        let rank = 1
        for (let contestant of contestants) {
            if (contestant.contestant.id === this.props.contestant.id) {
                return rank;
            }
            rank += 1
        }
        return -1
    }

    componentDidUpdate(prevProps) {
        this.scrollToBottom()
    }

    scrollToBottom = () => {
        this.messagesEnd.scrollIntoView({behavior: "smooth"});
    }

    resetToAllContestants() {
        this.props.setDisplay({displayType: SIMPLE_RANK_DISPLAY})
        this.props.displayAllTracks();
        this.props.hideLowerThirds();
    }

    render() {
        const progress = Math.min(100, Math.max(0, this.props.progress.toFixed(1)))
        const finished = this.props.contestantData.current_state === "Finished"
        let projectedScore = calculateProjectedScore(this.props.contestantData.score, progress).toFixed(0)
        if (projectedScore === "99999") {
            projectedScore = "--"
        }
        const columns = [
            {
                text: "",
                headerFormatter: (column, colIndex, components) => {
                    return <div>PLACE<br/>{ordinal_suffix_of(this.calculateRank())}</div>

                },
                headerClasses: "text-center",
                dataField: "message.gate",
                formatter: (cell, row) => {
                    return <b>{cell}</b>
                },
                headerEvents: {
                    onClick: (e, column, columnIndex) => {
                        this.resetToAllContestants()
                    }
                }
            },
            {
                dataField: "message",
                text: "",
                headerFormatter: (column, colIndex, components) => {
                    return <div className={"contestant-details-header"}>
                        <div className={"row"}>
                            <div className={"col-6"}>{contestantTwoLines(this.props.contestant)}</div>
                            <div className={"col-2 text-center"}
                                 style={{color: "#e01b1c"}}>SCORE<br/>{this.props.contestantData.score.toFixed(2)}</div>
                            <div className={"col-2 text-center"} style={{color: "orange"}}>EST<br/>{projectedScore}
                            </div>
                            <div className={"col-2 details-progress-circle"} style={{paddingTop: "5px"}}><ProgressCircle
                                progress={progress}
                                finished={finished}/>
                            </div>
                        </div>
                    </div>
                },
                formatter: (cell, row) => {
                    return <div className={"preWrap"}><FormatMessage message={cell}/></div>
                },
                headerEvents: {
                    onClick: (e, column, columnIndex) => {
                        this.resetToAllContestants()
                    }
                }
            }
        ]
        if (!this.props.contestantData) {
            return <div/>
        }
        const events = this.props.contestantData.score_log.map((line, index) => {
            return {
                key: this.props.contestantData.contestant_id + "details" + index,
                message: line,
            }
        })

        const paginationOptions = {
            sizePerPage: 20,
            hideSizePerPage: true,
            hidePageListOnlyOnePage: true
        };
        const rowEvents = {
            onClick: (e, row, rowIndex) => {
                this.resetToAllContestants()
            }
        }

        const loading = this.props.initialLoading ? <Loading/> : <div/>
        return <div>
            {loading}
            <BootstrapTable keyField={"key"} data={events} columns={columns}
                            classes={"table-dark"} wrapperClasses={"text-dark bg-dark"}
                            bootstrap4 striped hover condensed rowEvents={rowEvents}
                            bordered={false}//pagination={paginationFactory(paginationOptions)}
            />
            <div style={{float: "left", clear: "both"}}
                 ref={(el) => {
                     this.messagesEnd = el;
                 }}>
            </div>
        </div>

    }
}

const ContestantDetailsDisplay = connect(mapStateToProps, {
    setDisplay,
    displayAllTracks,
    hideLowerThirds
})(ConnectedContestantDetailsDisplay)
export default ContestantDetailsDisplay