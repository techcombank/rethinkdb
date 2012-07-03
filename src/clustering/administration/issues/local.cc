#include "clustering/administration/issues/local.hpp"

#include "utils.hpp"
#include "clustering/administration/persist.hpp"

local_issue_t::local_issue_t(const std::string& _type, bool _critical, const std::string& _description)
        : type(_type), critical(_critical), description(_description), timestamp(get_secs()) { }

local_issue_t *local_issue_t::clone() const {
    local_issue_t *ret = new local_issue_t(type, critical, description);
    ret->timestamp = timestamp;
    return ret;
}