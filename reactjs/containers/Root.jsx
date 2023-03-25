import 'react-app-polyfill/ie9';
import 'react-app-polyfill/stable'
import React from "react";
import {Provider} from "react-redux";
import store from "../store/index";
import {BrowserRouter, Redirect, Route, withRouter} from "react-router-dom";
import Router from "../config/NavigationTaskRouter";

const root=createRoot(document.getElementById("root"))

root.render(
    <Provider store={store}>
                <BrowserRouter>
            <main>
                <Route path="/:url*" exact strict render={({location}) => <Redirect to={`${location.pathname}/`}/>}
                    // Redirect to trailing slash to avoid URL problems in children
                />
                <Route path="*" component={withRouter(Router)}/>
            </main>
        </BrowserRouter>
    </Provider>,
);