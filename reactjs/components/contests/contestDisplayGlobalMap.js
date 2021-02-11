import React, {Component} from "react";
import {connect} from "react-redux";

const L = window['L']

export const mapStateToProps = (state, props) => ({})
export const mapDispatchToProps = {}

class ConnectedContestDisplayGlobalMap extends Component {
    constructor(props) {
        super(props)
        this.circle = null
    }

    componentDidMount() {
        // this.props.fetchContestsNavigationTaskSummaries(this.props.contest.id)
        this.circle = L.circle([this.props.contest.latitude, this.props.contest.longitude], {
            radius: 50000,
            color: "red",
            opacity: 0.3
        }).bindTooltip(this.props.contest.name, {
            permanent: true,
            direction: "center"
        }).openTooltip().addTo(this.props.map)
    }

    componentWillUnmount() {
        this.circle.removeFrom(this.props.map)
    }

    render() {
        return null
    }
}

const ContestDisplayGlobalMap = connect(mapStateToProps, mapDispatchToProps)(ConnectedContestDisplayGlobalMap);
export default ContestDisplayGlobalMap;