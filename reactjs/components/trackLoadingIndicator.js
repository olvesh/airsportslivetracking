import React, {Component} from "react";
import ProgressBar from "react-bootstrap/ProgressBar";
import {connect} from "react-redux";

const mapStateToProps = (state, props) => ({
    initialLoading: state.initialLoadingContestantData,
})


class ConnectedTrackLoadingIndicator extends Component {
    getPercentageCompletedLoading() {
        let count = 0;
        Object.keys(this.props.initialLoading).map((key, index) => {
            if (!this.props.initialLoading[key]) {
                count++;
            }
        })
        return Math.round(100 * count / this.props.numberOfContestants)
    }

    render() {
        const now = this.getPercentageCompletedLoading();
        const loading = now !== 100 ? <ProgressBar now={now} label={now + "%"}/> : <div/>
        return loading
    }
}

const TrackLoadingIndicator = connect(mapStateToProps)(ConnectedTrackLoadingIndicator);
export default TrackLoadingIndicator;