import 'regenerator-runtime/runtime'
import NavigationTask from "./navigationTask";
import {connect} from "react-redux";
import React, {Component} from "react";
import TrackLoadingIndicator from "./trackLoadingIndicator";
import {LowerThirdTeam} from "./teamBadges";
import {displayAllTracks, expandTrackingTable, hideLowerThirds, setDisplay, shrinkTrackingTable} from "../actions";
import {SIMPLE_RANK_DISPLAY} from "../constants/display-types";

// import "leaflet/dist/leaflet.css"

const mapStateToProps = (state, props) => ({
    navigationTask: state.navigationTask,
    displayExpandedTrackingTable: state.displayExpandedTrackingTable,
    displayLowerThirds: state.displayLowerThirds,
    contestants: state.contestants,
    currentDisplay: state.currentDisplay,
})

class ConnectedTrackingContainer extends Component {
    constructor(props) {
        super(props);
        this.client = null;
        this.viewer = null;
        this.map = null;
        this.navigationTaskId = document.configuration.navigation_task_id;
        this.contestId = document.configuration.contest_id;
        this.displayMap = document.configuration.displayMap;
        this.displayTable = document.configuration.displayTable;
        this.resetToAllContestants = this.resetToAllContestants.bind(this)
    }

    resetToAllContestants() {
        this.props.setDisplay({displayType: SIMPLE_RANK_DISPLAY})
        this.props.displayAllTracks();
        this.props.hideLowerThirds();
    }

    render() {
        const TrackerDisplay =
            <NavigationTask map={this.map} contestId={this.contestId} navigationTaskId={this.navigationTaskId}
                            fetchInterval={2000}
                            displayMap={this.displayMap} displayTable={true}/>
        if (this.displayTable && this.displayMap) {
            return (
                <div id="map-holder">
                    <div id='main_div' className={"fill"}>
                        <div className={"row fill ml-1"}>
                            <div className={"col-5"}>
                                {TrackerDisplay}
                            </div>
                            <div className={"col-7 fill"}>
                                <div id="cesiumContainer"/>
                                {/*<div id="logoContainer"><img src={"/static/img/AirSportsLogo.png"} className={"img-fluid"}/>*/}
                                {/*</div>*/}
                            </div>
                        </div>
                    </div>
                </div>
            );
        } else if (this.displayTable) {
            return (
                <div id="map-holder">
                    <div id='main_div' className={"fill"}>
                        <div className={"row fill ml-1"}>
                            <div className={"col-12"}>
                                {TrackerDisplay}
                            </div>
                        </div>
                    </div>
                </div>
            );
        } else {
            return (
                <div id="map-holder">
                    <div id='main_div' className={"fill"}>
                        {this.props.navigationTask.contestant_set ? <TrackLoadingIndicator
                            numberOfContestants={this.props.navigationTask.contestant_set.length}/> : <div/>}
                        <div className={"row fill ml-1"}>
                            <div
                                className={"titleWrapper " + (this.props.displayExpandedTrackingTable ? "largeTitle" : "compactTitle")}>
                                <a className={"btn"} data-toggle={"collapse"} data-target={"#insetMenu"}>
                                    {/*id={"logoButtonWrapper"}>*/}
                                    <img id={'menuButton'}
                                         alt={"Menu toggle"}
                                         src={"/static/img/menubutton.png"}/>
                                </a>
                                <a href={"#"} className={'taskTitle'}
                                   onClick={this.resetToAllContestants}>{this.props.navigationTask.name}</a>
                                {this.props.currentDisplay.displayType === SIMPLE_RANK_DISPLAY ?
                                    <a className={"shrinkLink taskTitle"} href={"#"}
                                       onClick={this.props.displayExpandedTrackingTable ? this.props.shrinkTrackingTable : this.props.expandTrackingTable}>{this.props.displayExpandedTrackingTable ? "<<<" : ">>>"}</a> : null}

                            </div>
                            <a className={"btn"} id="returnLink" href={"/"}><img alt={"Back to main page"}
                                                                                 id={"returnLinkImage"}
                                                                                 src={"/static/img/airsports.png"}/></a>
                            <div id="cesiumContainer"/>
                            <div
                                className={"backdrop " + (this.props.displayExpandedTrackingTable ? "largeTable" : "compactTable")}>{TrackerDisplay}</div>
                            {this.props.displayLowerThirds !== null ?
                                <LowerThirdTeam
                                    contestant={this.props.contestants[this.props.displayLowerThirds]}/> : null}

                            {/*<div id="logoContainer"><img src={"/static/img/AirSportsLogo.png"} className={"img-fluid"}/>*/}
                            {/*</div>*/}
                        </div>
                    </div>
                </div>
            )
        }
    }
}

const TrackingContainer = connect(mapStateToProps, {
    expandTrackingTable,
    shrinkTrackingTable,
    setDisplay,
    displayAllTracks,
    hideLowerThirds
})(ConnectedTrackingContainer)
export default TrackingContainer