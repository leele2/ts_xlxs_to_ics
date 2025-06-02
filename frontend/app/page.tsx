import ShiftCalendarUploader from "./components/ShiftCalendarUploader";
import { Providers } from "./components/Provider";

export default function Home() {
    return (
        <Providers>
            <ShiftCalendarUploader />
        </Providers>
    );
}
